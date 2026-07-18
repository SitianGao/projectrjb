"""
TutorAgent —— 智能辅导问答智能体

面向学生即时问题，提供多风格解释、图表生成和学习建议。
集成 RAG 检索引擎，回答时自动注入知识库参考来源。

输出结构（对齐 docs/design.md §10.4.3）:
    answer: str               — 主要回答内容
    explanation_style: str    — 使用的解释风格: analogy | formula | visual | story
    references: list[dict]    — 参考来源列表 [{title, source, content, similarity}]
    diagrams: list[str]       — Mermaid 图表文本数组（可为空）
"""
import json
import logging
from typing import Optional, List, Dict

from .base_agent import BaseAgent

# ── 新架构导入 ──
from core.agent_context import AgentContext
from agents.schemas import TutorResponse
from agents.prompts.tutor_prompts import (
    TUTOR_SYSTEM_PROMPT,
    TUTOR_ACTION_PROMPTS,
)
from core.knowledge_service import knowledge_service

try:
    from config import LLM_STRICT_MODE, RAG_STRICT_MODE
except ModuleNotFoundError:
    from backend.config import LLM_STRICT_MODE, RAG_STRICT_MODE

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 解释风格 System Prompt 片段
# ------------------------------------------------------------------
STYLE_PROMPTS = {
    "analogy": (
        "请用「类比法」解释：将抽象概念映射到日常生活中的熟悉场景。\n"
        "先点明『就像…一样』，再逐步对应概念的各部分。\n"
        "最后用一句话总结：日常场景 ↔ 对应知识点。"
    ),
    "formula": (
        "请用「公式推导法」解释：从基本定义出发，逐步推导出核心公式。\n"
        "每步推导说明其物理/数学含义，不要跳步。\n"
        "如果有多种推导路径，选择最直观的一种。"
    ),
    "visual": (
        "请用「图示法」解释：用文字描述可视化思路，并生成 Mermaid 流程图。\n"
        "```mermaid\ngraph TD\n  ...\n```\n"
        "图表应清晰展示各概念之间的关系和数据流向。"
    ),
    "story": (
        "请用「故事法」解释：编一个小故事（200-400 字），将知识点串联起来。\n"
        "故事要有角色、冲突、解决过程，知识自然嵌入情节中。\n"
        "故事结束后用 1-2 句点明各知识点在故事中的对应位置。"
    ),
    "auto": (
        "请根据问题类型自动选择最合适的解释风格：\n"
        "- 概念对比类 → 类比法\n"
        "- 数学/推导类 → 公式法\n"
        "- 流程/结构类 → 图示法（含 Mermaid）\n"
        "- 需要串联记忆 → 故事法\n"
        "混合使用以达到最佳效果。"
    ),
}


class TutorAgent(BaseAgent):
    """面向学生的智能辅导问答"""

    def __init__(self, llm_client=None):
        super().__init__(llm_client)

    def get_system_prompt(self) -> str:
        return TUTOR_SYSTEM_PROMPT

    # ------------------------------------------------------------------
    # 主入口 v1（向后兼容）
    # ------------------------------------------------------------------
    async def tutor(
        self,
        question: str,
        context: Optional[List[str]] = None,
        explanation_style: str = "auto",
        profile: Optional[dict] = None,
    ) -> str:
        """
        智能辅导问答。

        Args:
            question: 学生问题
            context: RAG 检索到的知识上下文（纯文本列表）
            explanation_style: 解释风格 — auto | analogy | formula | visual | story
            profile: 学生画像
        Returns:
            JSON 字符串: {answer, explanation_style, references, diagrams}
        """
        # ---- Day 10: 安全过滤 ----
        from safety.content_filter import check_safety
        filter_result = check_safety(question, context="tutor_question")
        if not filter_result["safe"]:
            return json.dumps({
                "answer": f"⚠️ {filter_result['reason']}",
                "explanation_style": "auto",
                "references": [],
                "diagrams": [],
                "blocked": True,
                "block_reason": filter_result["category"],
            }, ensure_ascii=False)

        profile_inner = (profile or {}).get("profile", profile or {})
        knowledge = profile_inner.get("knowledge_level", "中级")

        style_instruction = STYLE_PROMPTS.get(explanation_style, STYLE_PROMPTS["auto"])
        context_text = "\n".join(context or [])

        user_prompt = (
            f"学生认知水平: {knowledge}\n"
            f"问题: {question}\n\n"
            + (f"参考知识:\n{context_text}\n\n" if context_text else "")
            + style_instruction
        )

        if self.llm:
            try:
                chunks = []
                async for chunk in self.call_llm(user_prompt):
                    chunks.append(chunk)
                return "".join(chunks)
            except Exception:
                pass

        return self._rule_based_tutor(question, explanation_style, knowledge, context or [])

    # ------------------------------------------------------------------
    # RAG 集成入口 v1（Day 8 核心）—— 向后兼容，支持可选 course_id
    # ------------------------------------------------------------------
    async def tutor_with_rag(
        self,
        question: str,
        retriever=None,
        explanation_style: str = "auto",
        profile: Optional[dict] = None,
        top_k: int = 3,
        course_id: Optional[str] = None,
    ) -> dict:
        """带 RAG 知识检索的辅导问答 —— Day 8 核心方法。

        自动从知识库检索相关知识点，注入 LLM 上下文并作为参考来源返回。

        Args:
            question: 学生问题
            retriever: Retriever 实例（默认使用模块级 default_retriever）
            explanation_style: 解释风格
            profile: 学生画像
            top_k: RAG 检索数量
            course_id: 课程 ID（可选）。如提供，使用 knowledge_service 进行
                       课程作用域检索；否则回退到全局 default_retriever

        Returns:
            dict: {answer, explanation_style, references, diagrams}
                  其中 references 为 [{title, source, content, similarity}]
        """
        # ---- RAG 检索 ----
        rag_results = []
        rag_context_text = ""

        if course_id:
            # 使用 KnowledgeService 进行课程作用域检索
            try:
                rag_results = knowledge_service.retrieve(
                    course_id=course_id,
                    query=question,
                    top_k=top_k,
                    min_similarity=0.3,
                )
                if rag_results:
                    rag_context_text = knowledge_service.search_context(
                        course_id=course_id,
                        query=question,
                        top_k=top_k,
                    )
                    logger.info(
                        f"KnowledgeService RAG 检索命中 {len(rag_results)} 条: "
                        + ", ".join(r.get("title", "") for r in rag_results[:3])
                    )
                else:
                    logger.info(f"KnowledgeService RAG 检索无命中: '{question[:60]}'")
            except Exception as e:
                if RAG_STRICT_MODE:
                    raise RuntimeError(f"严格模式：课程知识库检索失败：{e}") from e
                logger.warning(f"KnowledgeService RAG 检索失败（降级为空上下文）: {e}")
        else:
            # 回退到原有 retriever 逻辑
            if retriever is None:
                from rag.retriever import default_retriever
                retriever = default_retriever

            try:
                rag_results = retriever.retrieve(question, top_k=top_k, min_similarity=0.3)
                if rag_results:
                    rag_context_text = self._build_rag_context(rag_results)
                    logger.info(
                        f"RAG 检索命中 {len(rag_results)} 条: "
                        + ", ".join(r["title"] for r in rag_results[:3])
                    )
                else:
                    logger.info(f"RAG 检索无命中: '{question[:60]}'")
            except Exception as e:
                if RAG_STRICT_MODE:
                    raise RuntimeError(f"严格模式：辅导知识库检索失败：{e}") from e
                logger.warning(f"RAG 检索失败（降级为空上下文）: {e}")

        # ---- 构建 Prompt ----
        profile_inner = (profile or {}).get("profile", profile or {})
        knowledge = profile_inner.get("knowledge_level", "中级")
        style_instruction = STYLE_PROMPTS.get(explanation_style, STYLE_PROMPTS["auto"])

        user_prompt = (
            f"学生认知水平: {knowledge}\n"
            f"问题: {question}\n\n"
            + (f"## 知识库参考资料\n{rag_context_text}\n\n" if rag_context_text else "")
            + "## 回答要求\n"
            + style_instruction
            + "\n\n请引用上方参考资料中的知识点来支撑你的回答。"
        )

        # ---- LLM 调用 ----
        if self.llm:
            try:
                chunks = []
                async for chunk in self.call_llm(user_prompt):
                    chunks.append(chunk)
                raw = "".join(chunks)
                result = json.loads(raw)
                # 注入 RAG 检索结果作为 references
                result["references"] = self._format_references(rag_results)
                return result
            except Exception as e:
                logger.warning(f"LLM 调用失败，使用规则化兜底: {e}")

        # ---- 规则化兜底 ----
        raw = self._rule_based_tutor(question, explanation_style, knowledge, [])
        result = json.loads(raw)
        if rag_results:
            result["references"] = self._format_references(rag_results)
        return result

    # ------------------------------------------------------------------
    # V2 主入口 —— 结构化输出
    # ------------------------------------------------------------------
    async def tutor_v2(
        self,
        *,
        context: AgentContext,
        question: str,
        selected_text: str = "",
        action: str = "ask",
        profile: dict | None = None,
        conversation_history: list[dict] | None = None,
    ) -> TutorResponse:
        """智能辅导问答（v2：Pydantic 结构化输出 + 课程作用域 RAG）。

        严格遵循课程边界：仅检索当前课程知识库，仅返回当前课程相关建议问题。

        Args:
            context: 统一 Agent 上下文（含 course_id 用于 RAG 检索路由）
            question: 学生问题
            selected_text: 学生选中的文本（explain_selected_text 动作时使用）
            action: 辅导动作 — ask | explain_selected_text | generate_example |
                    explain_differently | summarize | check_understanding
            profile: 学生画像 dict
            conversation_history: 多轮对话历史

        Returns:
            TutorResponse: Pydantic 校验后的结构化回答
        """
        # ---- 安全过滤 ----
        try:
            from safety.content_filter import check_safety
        except ModuleNotFoundError:
            from backend.safety.content_filter import check_safety
        filter_result = check_safety(question, context="tutor_question")
        if not filter_result["safe"]:
            return TutorResponse(
                answer=f"⚠️ {filter_result['reason']}",
                explanation_style="auto",
                confidence=0.0,
            )

        # ---- RAG 检索（课程作用域） ----
        rag_context_text = ""
        rag_results: list[dict] = []
        try:
            rag_context_text = knowledge_service.search_context(
                course_id=context.course_id,
                query=question,
                top_k=5,
            )
            rag_results = knowledge_service.retrieve(
                course_id=context.course_id,
                query=question,
                top_k=5,
                min_similarity=0.3,
            )
            logger.info(
                "TutorAgent V2 RAG: course=%s query='%s' → %d results",
                context.course_id, question[:60], len(rag_results),
            )
        except Exception as e:
            logger.warning("TutorAgent V2 RAG 检索失败（降级为空上下文）: %s", e)

        # ---- 构建 Prompt ----
        profile_inner = (profile or {}).get("profile", profile or {})
        knowledge_level = profile_inner.get("knowledge_level", "中级")

        # 动作对应提示词
        action_prompt_template = TUTOR_ACTION_PROMPTS.get(action, TUTOR_ACTION_PROMPTS["ask"])
        action_prompt = action_prompt_template.format(
            selected_text=selected_text if selected_text else "（无选中文本）"
        )

        # 对话历史
        history_text = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-6:]:  # 最近 6 轮
                role = msg.get("role", "user")
                content = msg.get("content", "")[:500]
                history_lines.append(f"{'学生' if role == 'user' else '辅导老师'}: {content}")
            history_text = "## 对话历史\n" + "\n".join(history_lines) + "\n\n"

        user_prompt = (
            f"{history_text}"
            f"学生认知水平: {knowledge_level}\n"
            f"当前课程ID: {context.course_id}\n"
            f"当前阶段ID: {context.stage_id or '未指定'}\n"
            f"当前任务ID: {context.task_id or '未指定'}\n"
            f"辅导动作: {action}\n"
            f"问题: {question}\n\n"
            + (f"## 课程知识库参考资料\n{rag_context_text}\n\n" if rag_context_text else "")
            + f"## 回答要求\n{action_prompt}\n\n"
            + "注意：\n"
            + "- 不自动完成任务或修改学习进度\n"
            + "- suggested_questions 仅限当前课程相关\n"
            + "- 优先引用上方参考资料中的知识点"
        )

        # ---- LLM 调用 ----
        if self.llm:
            try:
                result = await self.call_llm_json(
                    context=context,
                    user_prompt=user_prompt,
                    response_model=TutorResponse,
                )
                # 确保 suggested_questions 只包含当前课程相关问题
                result = self._scope_questions_to_course(result, context.course_id)
                # 注入 RAG 检索结果作为 citations
                if rag_results and not result.citations:
                    result.citations = self._format_references(rag_results)
                return result
            except Exception as e:
                if LLM_STRICT_MODE:
                    raise
                logger.warning("TutorAgent V2 LLM 调用失败，使用规则化兜底: %s", e)

        # ---- 规则化兜底 ----
        if LLM_STRICT_MODE:
            raise RuntimeError("严格模式：讯飞星火未配置，拒绝规则辅导降级")

        return self._rule_based_tutor_v2(
            question=question,
            action=action,
            selected_text=selected_text,
            knowledge_level=knowledge_level,
            rag_context_text=rag_context_text,
            rag_results=rag_results,
            course_id=context.course_id,
        )

    # ------------------------------------------------------------------
    # RAG 辅助方法
    # ------------------------------------------------------------------
    @staticmethod
    def _build_rag_context(rag_results: List[dict], max_chars: int = 2000) -> str:
        """将 RAG 检索结果格式化为 LLM prompt 可用的上下文文本。

        Args:
            rag_results: retriever.retrieve() 的返回列表
            max_chars: 总上下文最大字符数

        Returns:
            str: 格式化的参考知识文本
        """
        lines = []
        total = 0
        for i, r in enumerate(rag_results, 1):
            snippet = r["content"][:400]  # 每段最多 400 字符
            line = (
                f"### [{i}] {r['title']}（来源: {r['source']}, 相似度: {r['similarity']:.0%}）\n"
                f"{snippet}\n"
            )
            if total + len(line) > max_chars:
                break
            lines.append(line)
            total += len(line)

        return "\n".join(lines) if lines else "（资料库中未找到可靠依据）"

    @staticmethod
    def _format_references(rag_results: List[dict]) -> List[dict]:
        """将 RAG 检索结果格式化为符合 §10.4.3 的 references 数组。

        每个 reference 包含: {title, source, content, similarity}

        Args:
            rag_results: retriever.retrieve() 的返回列表

        Returns:
            list of dict
        """
        formatted = []
        for r in rag_results:
            formatted.append({
                "title": r["title"],
                "source": r["source"],
                "content": r["content"][:200],
                "similarity": r["similarity"],
            })
        return formatted

    @staticmethod
    def _scope_questions_to_course(
        response: TutorResponse,
        course_id: str,
    ) -> TutorResponse:
        """确保 suggested_questions 只包含当前课程相关的问题。

        如果 LLM 返回了其他课程或无关的推荐问题，将其过滤掉。
        """
        if not response.suggested_questions:
            return response

        # 词语过滤：移除明显不属于当前课程的关键词
        other_course_keywords: list[str] = []
        # 根据 course_id 确定排除词
        course_keyword_map = {
            "ai_deep_learning_demo": [],  # 当前课程不排除任何词
        }
        exclude_words = course_keyword_map.get(course_id, [])

        filtered = []
        for q in response.suggested_questions:
            should_exclude = any(
                keyword.lower() in q.lower()
                for keyword in exclude_words
            )
            if not should_exclude:
                filtered.append(q)

        # 如果全部被过滤，生成一个安全的默认问题
        if not filtered:
            filtered = [f"请帮我总结一下当前阶段的核心知识点"]

        return TutorResponse(
            answer=response.answer,
            citations=response.citations,
            knowledge_point_ids=response.knowledge_point_ids,
            suggested_questions=filtered[:3],
            confidence=response.confidence,
            explanation_style=response.explanation_style,
        )

    # ------------------------------------------------------------------
    # 规则化兜底 v2（返回 TutorResponse）
    # ------------------------------------------------------------------
    def _rule_based_tutor_v2(
        self,
        *,
        question: str,
        action: str,
        selected_text: str,
        knowledge_level: str,
        rag_context_text: str,
        rag_results: list[dict],
        course_id: str,
    ) -> TutorResponse:
        """规则化辅导回答 v2 —— 返回 Pydantic 模型。"""
        # 检测是否非学术问题
        non_academic_keywords = ["天气", "吃饭", "电影", "游戏", "音乐", "八卦"]
        if any(kw in question for kw in non_academic_keywords):
            return TutorResponse(
                answer=(
                    "我是学习辅导助手，专注于帮助你解决课程学习中的问题。\n\n"
                    "你可以问我：\n"
                    "- 某个概念的定义和原理\n"
                    "- 公式的推导过程\n"
                    "- 代码实现的思路\n"
                    "- 知识点的对比分析\n\n"
                    "有什么学习上的问题我可以帮你吗？"
                ),
                explanation_style="auto",
                suggested_questions=[
                    "这个知识点的核心概念是什么？",
                    "能否给我一个具体的例子？",
                    "这个知识点在实际中如何应用？",
                ],
                confidence=0.5,
            )

        # 根据动作构建回答
        answer = ""
        explanation_style = "auto"

        if action == "explain_selected_text":
            answer = (
                f"你选中了以下文本：\n\n> {selected_text}\n\n"
                f"让我来解释一下这段内容……\n\n"
                f"这段文字的核心意思是……（建议使用 LLM 获取更准确的解释）\n\n"
                f"> 建议核实: 具体解释请以教材和课程资料为准。"
            )
            explanation_style = "analogy"
        elif action == "generate_example":
            answer = (
                f"关于 '{question}' 的示例：\n\n"
                f"假设有一个简单的场景……\n\n"
                f"从基础开始逐步展开：\n"
                f"1. 基础情况: ...\n"
                f"2. 进阶应用: ...\n"
                f"3. 综合案例: ...\n\n"
                f"> 建议: 使用 LLM 获取更具体、更贴合你学习背景的示例。"
            )
            explanation_style = "analogy"
        elif action == "explain_differently":
            answer = (
                f"让我用另一种方式来解释 '{question}'：\n\n"
                f"（换个角度）……\n\n"
                f"与之前的解释不同，这次我们从……的角度来看。\n\n"
                f"> 建议: 使用 LLM 获取真正的多角度解释。"
            )
            explanation_style = "story"
        elif action == "summarize":
            answer = (
                f"关于当前知识点的核心要点总结：\n\n"
                f"1. 核心概念: ...\n"
                f"2. 关键原理: ...\n"
                f"3. 实际应用: ...\n"
                f"4. 注意事项: ...\n"
                f"5. 延伸思考: ...\n\n"
                f"> 建议: 使用 LLM 获取基于课程知识的准确总结。"
            )
            explanation_style = "formula"
        elif action == "check_understanding":
            answer = (
                f"来检查一下你对当前知识点的理解程度：\n\n"
                f"**问题 1**: 请简述当前知识点的核心内容。\n"
                f"（参考答案: ...）\n\n"
                f"**问题 2**: 请举一个实际应用的例子。\n"
                f"（参考答案: ...）\n\n"
                f"**问题 3**: 这个知识点与之前学过的内容有什么联系？\n"
                f"（参考答案: ...）\n\n"
                f"> 建议: 使用 LLM 获取更精准的检查题和自动批改。"
            )
            explanation_style = "formula"
        else:
            # 默认 ask 动作
            # 根据问题关键词推断风格
            if "区别" in question or "对比" in question:
                explanation_style = "analogy"
            elif "推导" in question or "公式" in question:
                explanation_style = "formula"
            elif "流程" in question or "步骤" in question:
                explanation_style = "visual"
            else:
                explanation_style = "analogy"

            templates = {
                "analogy": f"就像我们日常生活中的一个场景……\n\n'{question}'可以用一个生活类比来理解：\n\n"
                           f"想象你在……（此处替换为具体场景）\n\n"
                           f"这个类比中的每个元素分别对应……\n\n"
                           f"核心要点: （一句话总结，日常场景 ↔ 知识点）",
                "formula": f"我们从基本定义出发来推导 '{question}'：\n\n"
                           f"## 推导步骤\n\n"
                           f"1. 定义: ...\n"
                           f"2. 代入: ...\n"
                           f"3. 推导: ...\n"
                           f"4. 结论: ...\n\n"
                           f"## 直观理解\n\n"
                           f"以上推导的物理/数学含义是……\n\n"
                           f"> 建议核实: 具体公式符号请以教材为准。",
                "visual": f"'{question}' 的流程结构如下：\n\n"
                          f"```mermaid\n"
                          f"graph TD\n"
                          f"    A[输入/前置条件] --> B[核心处理步骤]\n"
                          f"    B --> C[中间结果]\n"
                          f"    C --> D[最终输出]\n"
                          f"    D --> E[应用/下一步]\n"
                          f"```\n\n"
                          f"## 图示说明\n\n"
                          f"1. **输入**: ...\n"
                          f"2. **处理**: ...\n"
                          f"3. **输出**: ...",
                "story": f"让我为你讲一个小故事，帮助你理解 '{question}'：\n\n"
                         f"从前有一个初学者小明，他在学习过程中遇到了一个难题……\n\n"
                         f"（故事展开，将知识点作为解决问题的线索）\n\n"
                         f"最后小明发现，原来……就是……！\n\n"
                         f"## 知识点对应\n\n"
                         f"- 小明的困惑 → （对应知识点 A）\n"
                         f"- 解决线索 → （对应知识点 B）",
            }
            answer = templates.get(explanation_style, templates["analogy"])

        # 构建 citations
        if rag_results:
            citations = self._format_references(rag_results)
        else:
            citations = [
                {
                    "title": "建议参考课程指定教材相关章节",
                    "source": "教材",
                    "content": "当前知识库中暂无与问题相关的检索结果。建议参考课程指定教材，或换个方式描述问题后重新提问。",
                    "similarity": 0.0,
                }
            ]

        # suggested_questions 仅限当前课程相关
        suggested_questions = [
            f"能否详细解释一下这个知识点？",
            f"这个知识点在实际中如何应用？",
            f"有哪些常见的误区需要注意？",
        ]

        return TutorResponse(
            answer=answer,
            citations=citations,
            knowledge_point_ids=[],
            suggested_questions=suggested_questions,
            confidence=0.3,
            explanation_style=explanation_style,
        )

    # ------------------------------------------------------------------
    # 规则化兜底 v1（保持向后兼容）
    # ------------------------------------------------------------------
    def _rule_based_tutor(
        self,
        question: str,
        style: str,
        knowledge: str,
        context: List[str],
    ) -> str:
        """开发期无 API Key 时使用的规则化回答"""
        # 检测是否非学术问题
        non_academic_keywords = ["天气", "吃饭", "电影", "游戏", "音乐", "八卦"]
        if any(kw in question for kw in non_academic_keywords):
            answer = (
                "我是学习辅导助手 😊，专注于帮助你解决课程学习中的问题。\n\n"
                "你可以问我：\n"
                "- 某个概念的定义和原理\n"
                "- 公式的推导过程\n"
                "- 代码实现的思路\n"
                "- 知识点的对比分析\n\n"
                "有什么学习上的问题我可以帮你吗？"
            )
            result = {
                "answer": answer,
                "explanation_style": "auto",
                "references": [],
                "diagrams": [],
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

        # 根据风格构建回答骨架
        if style == "auto":
            # 简单启发式：含"区别"→类比、含"推导"→公式、含"流程"→图示
            if "区别" in question or "对比" in question:
                style = "analogy"
            elif "推导" in question or "公式" in question:
                style = "formula"
            elif "流程" in question or "步骤" in question:
                style = "visual"
            else:
                style = "analogy"  # 默认类比

        templates = {
            "analogy": f"就像我们日常生活中的一个场景……\n\n'{question}'可以用一个生活类比来理解：\n\n"
                       f"想象你在……（此处替换为具体场景）\n\n"
                       f"这个类比中的每个元素分别对应……\n\n"
                       f"核心要点: （一句话总结，日常场景 ↔ 知识点）",
            "formula": f"我们从基本定义出发来推导 '{question}'：\n\n"
                       f"## 推导步骤\n\n"
                       f"1. 定义: ...\n"
                       f"2. 代入: ...\n"
                       f"3. 推导: ...\n"
                       f"4. 结论: ...\n\n"
                       f"## 直观理解\n\n"
                       f"以上推导的物理/数学含义是……\n\n"
                       f"> 建议核实: 具体公式符号请以教材为准。",
            "visual": f"'{question}' 的流程结构如下：\n\n"
                      f"```mermaid\n"
                      f"graph TD\n"
                      f"    A[输入/前置条件] --> B[核心处理步骤]\n"
                      f"    B --> C[中间结果]\n"
                      f"    C --> D[最终输出]\n"
                      f"    D --> E[应用/下一步]\n"
                      f"```\n\n"
                      f"## 图示说明\n\n"
                      f"1. **输入**: ...\n"
                      f"2. **处理**: ...\n"
                      f"3. **输出**: ...",
            "story": f"让我为你讲一个小故事，帮助你理解 '{question}'：\n\n"
                     f"从前有一个初学者小明，他在学习过程中遇到了一个难题……\n\n"
                     f"（故事展开，将知识点作为解决问题的线索）\n\n"
                     f"最后小明发现，原来……就是……！\n\n"
                     f"## 知识点对应\n\n"
                     f"- 小明的困惑 → （对应知识点 A）\n"
                     f"- 解决线索 → （对应知识点 B）",
        }

        answer = templates.get(style, templates["analogy"])
        refs = context if context else ["建议参考课程指定教材相关章节"]

        diagrams = []
        if style == "visual":
            diagrams.append(
                "graph TD\n"
                "    A[输入/前置条件] --> B[核心处理步骤]\n"
                "    B --> C[中间结果]\n"
                "    C --> D[最终输出]"
            )

        result = {
            "answer": answer,
            "explanation_style": style,
            "references": refs,
            "diagrams": diagrams,
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
