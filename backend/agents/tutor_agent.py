"""
TutorAgent —— 智能辅导问答智能体

面向学生即时问题，提供多风格解释、图表生成和学习建议。

输出结构（对齐 docs/design.md §10.4.3）:
    answer: str               — 主要回答内容
    explanation_style: str    — 使用的解释风格: analogy | formula | visual | story
    references: list[str]     — 参考来源列表
    diagrams: list[str]       — Mermaid 图表文本数组（可为空）
"""
import json
from typing import Optional, List, Dict

from .base_agent import BaseAgent


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
        base = (
            "你是智能辅导问答智能体。\n"
            "你的职责是回答学生在学习过程中的问题，用最适合的方式帮助他们理解。\n\n"
            "## 工作要求\n"
            "1. 根据学生认知水平调整解释难度：初级少用术语、中级适当公式、高级深入推导。\n"
            "2. 每回答一个问题，附带 1-2 个后续思考问题引导深入。\n"
            "3. 如果问题超出学术范围（如天气、闲聊），礼貌引导回学习主题。\n\n"
            "## 防幻觉约束\n"
            "1. 只回答你确定的内容，不确定请标注『建议核实』。\n"
            "2. 公式、定理、年份等务必核实准确性。\n"
            "3. 超出知识范围请诚实告知。\n"
            "4. 不生成违规、敏感或不安全的内容。\n\n"
            "## 输出格式\n"
            "严格输出 JSON: {answer, explanation_style, references, diagrams}\n"
            "- answer: 主回答 Markdown 文本\n"
            "- explanation_style: 实际使用的风格 (analogy|formula|visual|story)\n"
            "- references: 参考来源列表，至少 1 项\n"
            "- diagrams: Mermaid 图表文本列表，无图表时为空数组 []"
        )
        return base

    # ------------------------------------------------------------------
    # 主入口
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
            context: RAG 检索到的知识上下文
            explanation_style: 解释风格 — auto | analogy | formula | visual | story
            profile: 学生画像
        Returns:
            JSON 字符串: {answer, explanation_style, references, diagrams}
        """
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
    # 规则化兜底（无需 LLM）
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
