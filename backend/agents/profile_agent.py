"""
ProfileAgent v01 —— 基于 LLM 的学生画像构建智能体

职责：
- 通过自然语言对话提取学生画像（6+ 维度）
- 支持增量更新（多轮对话画像逐步完善）
- 提供非流式 build_profile() 供编排器使用
- 提供流式 chat() 供 SSE 端点使用
- v2: 提供 AgentContext 驱动的 build_profile_v2() 和 update_from_evaluation()

设计依据：docs/ai/agent-io.md §5 + docs/requirement.md §2.1(1)
"""
import json
import logging
import re
from datetime import datetime, timezone
from typing import AsyncIterator, Optional, List, Dict

from .base_agent import BaseAgent
from core.agent_context import AgentContext
from agents.schemas import ProfileOutput, CourseProfile, KnowledgeFoundation, WeakPoint
from agents.prompts.profile_prompts import PROFILE_SYSTEM_PROMPT, PROFILE_UPDATE_PROMPT

<<<<<<< Updated upstream
=======
try:
    from config import LLM_STRICT_MODE, PROFILE_READY_THRESHOLD
except ModuleNotFoundError:
    from backend.config import LLM_STRICT_MODE, PROFILE_READY_THRESHOLD

logger = logging.getLogger(__name__)

>>>>>>> Stashed changes

class ProfileAgent(BaseAgent):
    """学生画像构建智能体 —— LLM prompt v01"""

    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.name = "ProfileAgent"

    def get_system_prompt(self) -> str:
<<<<<<< Updated upstream
        """
        v01 prompt：指导学生画像提取

        核心要点：
        - 从对话中抽取 6 个维度：知识水平、学习目标、认知风格、薄弱点、兴趣、学习节奏
        - 支持增量更新：已有画像时只更新变化的部分
        - 输出严格 JSON，保证下游可解析
        - 诚实标注置信度，信息不足时降低 confidence
        """
        return (
            "你是一个学生画像构建智能体，专门通过自然语言对话分析学生学习特征。\n"
            "\n"
            "## 你的任务\n"
            "根据学生的对话内容和学习历史，提取以下 6 个维度的画像信息：\n"
            "\n"
            "1. **knowledge_level（知识水平）**：学生当前的知识基础和能力层次。\n"
            "   - 可选值示例：\"零基础\" / \"初级\" / \"中级\" / \"中高级\" / \"高级\"\n"
            "   - 需结合具体学科描述，如\"大二水平，Python基础扎实，数学较弱\"\n"
            "\n"
            "2. **learning_goal（学习目标）**：学生希望达成的学习目标。\n"
            "   - 越具体越好，如\"掌握机器学习基础算法并能独立完成Kaggle入门赛\"\n"
            "   - 如果学生表述模糊，如实记录并标注 confidence 较低\n"
            "\n"
            "3. **cognitive_style（认知风格）**：学生偏好的学习方式。\n"
            "   - 常见类型：\"视觉型（偏好图解/视频）\" / \"动手型（偏好代码/项目）\" / \"理论型（偏好推导/公式）\" / \"听觉型（偏好讲解/讨论）\"\n"
            "   - 可从学生的表达方式中推断（如反复提到\"看\"、\"做\"、\"推导\"等关键词）\n"
            "\n"
            "4. **weakness（薄弱点/易错点）**：学生自述或表现出的知识薄弱环节。\n"
            "   - 以 JSON 数组形式列出，如 [\"数学推导\", \"概率论\", \"RNN梯度消失\"]\n"
            "   - 如学生未提及，则为空数组 []\n"
            "\n"
            "5. **interest（兴趣方向）**：学生明确表达或隐含的兴趣领域。\n"
            "   - 以 JSON 数组形式列出，如 [\"计算机视觉\", \"NLP\", \"强化学习\"]\n"
            "   - 区分\"感兴趣\"和\"需要学\"——只记录前者\n"
            "\n"
            "6. **pace_preference（学习节奏偏好）**：学生倾向的学习速度和深度。\n"
            "   - 可选值示例：\"快速概览型\" / \"中速均衡型\" / \"慢速深入型\"\n"
            "   - 如未提及，默认\"中速均衡型\"\n"
            "\n"
            "## 输出格式（严格 JSON）\n"
            "你必须只输出一个 JSON 对象，不要包含任何其他文字。格式如下：\n"
            "```json\n"
            "{\n"
            '  "profile": {\n'
            '    "knowledge_level": "string",\n'
            '    "learning_goal": "string",\n'
            '    "cognitive_style": "string",\n'
            '    "weakness": ["string"],\n'
            '    "interest": ["string"],\n'
            '    "pace_preference": "string"\n'
            '  },\n'
            '  "completeness": 0.0~1.0,\n'
            '  "confidence": 0.0~1.0,\n'
            '  "sources": ["dialogue", "learning_history", ...],\n'
            '  "next_questions": ["问题1", "问题2"]\n'
            "}\n"
            "```\n"
            "\n"
            "## 增量更新规则\n"
            "如果对话中包含已有的画像数据（current_profile），请遵循以下规则：\n"
            "- 每个维度：新信息明确时更新，否则保持原值\n"
            "- weakness/interest：新增条目追加到已有数组，不覆盖\n"
            "- completeness：根据本次新增的信息量适度提升（每次 +0.05~0.15，上限 0.95）\n"
            "\n"
            "## 置信度标注\n"
            "- confidence ≥ 0.9：多个维度有明确信息支撑\n"
            "- confidence 0.7~0.9：部分维度有信息，部分为合理推断\n"
            "- confidence < 0.7：信息不足，多为默认填充\n"
            "\n"
            "## 追问策略\n"
            "当 completeness < 0.7 时，next_questions 中列出 2~3 个结构化追问，\n"
            "优先询问当前最缺的维度（薄弱点 > 学习目标 > 认知风格 > 兴趣 > 节奏）。\n"
            "当 completeness ≥ 0.85 时，next_questions 可以为空数组。\n"
            "\n"
            "## 防幻觉约束\n"
            "1. 仅基于学生实际表述提取画像，不猜测未提及的信息。\n"
            "2. 置信度诚实反映信息充分程度——信息不足时必须降低 confidence。\n"
            "3. 不编造学生的学习历史、成绩或弱点。\n"
            "4. 不生成违规、敏感或不安全的内容。\n"
            "5. 若学生输入超出学习范围（如闲聊、攻击性言论），礼貌引导回画像构建。\n"
        )
=======
        """返回标准化系统提示词（由 prompts 模块统一管理）。"""
        return PROFILE_SYSTEM_PROMPT
>>>>>>> Stashed changes

    # ---- 非流式：供编排器 pipeline 使用 ----

    async def build_profile(
        self,
        student_id: str,
        message: str,
        history: Optional[List[str]] = None,
        current_profile: Optional[Dict] = None,
        context: Optional[AgentContext] = None,
    ) -> Dict:
        """
        构建/更新学生画像（非流式，返回完整 dict）。

        Args:
            student_id: 学生唯一标识
            message: 当前轮用户消息
            history: 历史对话消息列表
            current_profile: 已有画像（增量更新时传入）
            context: 可选 AgentContext；未提供时自动从 student_id 构造

        Returns:
            dict: {
                "student_id": str,
                "profile": {...6 dimensions...},
                "completeness": float,
                "confidence": float,
                "sources": [...],
                "next_questions": [...]
            }
        """
        if context is None:
            course_id = "default"
            if current_profile:
                cp = current_profile.get("profile", current_profile)
                course_id = cp.get("course_id", "default") if isinstance(cp, dict) else "default"
            context = AgentContext(user_id=student_id, course_id=course_id)
        logger.info(
            "[ProfileAgent] build_profile user_id=%s course_id=%s",
            context.user_id, context.course_id,
        )

        # ---- Day 10: 安全过滤 ----
        from safety.content_filter import check_safety
        filter_result = check_safety(message, context="profile_message")
        if not filter_result["safe"]:
            return self._keyword_fallback(student_id, "请介绍你的学习情况", history or [])

        user_prompt = self._build_user_prompt(message, history, current_profile)

        # 尝试 LLM 调用
        try:
            full_response = []
            async for chunk in self.call_llm(user_prompt):
                full_response.append(chunk)
            raw = "".join(full_response)
            parsed = self._parse_llm_json(raw)
            if parsed:
                result = {
                    "student_id": student_id,
                    "profile": parsed.get("profile", {}),
                    "completeness": parsed.get("completeness", 0.3),
                    "confidence": parsed.get("confidence", 0.5),
                    "sources": parsed.get("sources", ["dialogue"]),
                    "next_questions": parsed.get("next_questions", []),
                }
                # 确保 learning_history 字段存在
                if "learning_history" not in result["profile"]:
                    result["profile"]["learning_history"] = history or []
                if not result["profile"].get("learning_history"):
                    result["profile"]["learning_history"] = history or []
                return result
        except Exception:
            pass  # fall through to fallback

        # 降级：关键字规则兜底
        return self._keyword_fallback(student_id, message, history or [])

    # ---- v2: AgentContext 驱动的结构化输出 ----

    async def build_profile_v2(
        self,
        *,
        context: AgentContext,
        message: str,
        history: list[str] | None = None,
        current_profile: dict | None = None,
    ) -> ProfileOutput:
        """
        构建/更新学生画像 —— v2 结构化版本。

        使用 call_llm_json 获取 Pydantic 校验后的 ProfileOutput。
        LLM 不可用或失败时，降级到关键字规则提取。

        Args:
            context: 统一 Agent 上下文（包含 user_id / course_id）
            message: 当前轮用户消息
            history: 历史对话消息列表
            current_profile: 已有画像 dict（增量更新时传入）

        Returns:
            ProfileOutput: 通过 Pydantic 校验的画像输出
        """
        logger.info(
            "[ProfileAgent] build_profile_v2 user_id=%s course_id=%s",
            context.user_id, context.course_id,
        )

        # ---- 安全过滤 ----
        try:
            from safety.content_filter import check_safety
        except ModuleNotFoundError:
            from backend.safety.content_filter import check_safety
        filter_result = check_safety(message, context="profile_message")
        if not filter_result["safe"]:
            if not LLM_STRICT_MODE:
                fallback_data = self._keyword_fallback(
                    context.user_id,
                    "请介绍你的学习情况",
                    history or [],
                    current_profile,
                )
                return self._legacy_dict_to_profile_output(context, fallback_data)
            raise ValueError(filter_result.get("reason") or "画像输入未通过安全检查")

        user_prompt = self._build_user_prompt(message, history, current_profile)

        # 尝试 LLM 结构化调用
        try:
            result = await self.call_llm_json(
                context=context,
                user_prompt=user_prompt,
                response_model=ProfileOutput,
            )
            # 确保 can_start_journey 与 completeness 一致
            if result.completeness >= PROFILE_READY_THRESHOLD:
                result.can_start_journey = True
                result.next_questions = []
            logger.info(
                "[ProfileAgent] build_profile_v2 LLM success user_id=%s course_id=%s completeness=%.2f",
                context.user_id, context.course_id, result.completeness,
            )
            return result
        except Exception as e:
            logger.warning(
                "[ProfileAgent] build_profile_v2 LLM failed user_id=%s course_id=%s: %s",
                context.user_id, context.course_id, e,
            )
            if LLM_STRICT_MODE:
                raise

        # 降级：关键字规则兜底 → ProfileOutput
        fallback_data = self._keyword_fallback(
            context.user_id, message, history or [], current_profile,
        )
        return self._legacy_dict_to_profile_output(context, fallback_data)

    async def update_from_evaluation(
        self,
        *,
        context: AgentContext,
        evaluation: dict,
        current_profile: dict,
    ) -> ProfileOutput:
        """
        根据评估结果更新课程画像。

        使用 PROFILE_UPDATE_PROMPT 指导 LLM 更新 weak_points 和
        knowledge_foundation。LLM 失败时降级为规则化更新。

        Args:
            context: 统一 Agent 上下文
            evaluation: 评估报告 dict（来自 EvaluateAgent）
            current_profile: 当前画像 dict

        Returns:
            ProfileOutput: 更新后的画像
        """
        logger.info(
            "[ProfileAgent] update_from_evaluation user_id=%s course_id=%s",
            context.user_id, context.course_id,
        )

        evaluation_json = json.dumps(evaluation, ensure_ascii=False, indent=2)
        current_profile_json = json.dumps(current_profile, ensure_ascii=False, indent=2)

        user_prompt = PROFILE_UPDATE_PROMPT.format(
            evaluation_json=evaluation_json,
            current_profile_json=current_profile_json,
        )

        try:
            result = await self.call_llm_json(
                context=context,
                user_prompt=user_prompt,
                response_model=ProfileOutput,
            )
            # 版本号递增
            result.profile.version = (current_profile.get("profile", {}).get("version", 0) if isinstance(current_profile, dict) else 0) + 1
            result.profile.updated_at = datetime.now(timezone.utc).isoformat()
            logger.info(
                "[ProfileAgent] update_from_evaluation LLM success user_id=%s course_id=%s",
                context.user_id, context.course_id,
            )
            return result
        except Exception as e:
            logger.warning(
                "[ProfileAgent] update_from_evaluation LLM failed user_id=%s course_id=%s: %s",
                context.user_id, context.course_id, e,
            )
            if LLM_STRICT_MODE:
                raise

        # 降级：规则化更新
        cp = current_profile.get("profile", current_profile) if isinstance(current_profile, dict) else {}
        if not isinstance(cp, dict):
            cp = {}
        existing_weak_points = cp.get("weak_points") or []
        existing_knowledge = cp.get("knowledge_foundation") or {}

        # 从评估中提取薄弱点并合并
        eval_weaknesses = evaluation.get("weaknesses") or []
        new_weak_points = list(existing_weak_points)
        existing_names = {wp.get("name", "") if isinstance(wp, dict) else getattr(wp, "name", "") for wp in existing_weak_points}
        for w in eval_weaknesses:
            if isinstance(w, dict):
                wname = w.get("name", "")
                if wname and wname not in existing_names:
                    new_weak_points.append({
                        "knowledge_point_id": w.get("knowledge_point_id", f"kp_eval_{len(new_weak_points)}"),
                        "name": wname,
                        "score": w.get("score", 50),
                    })
                    existing_names.add(wname)

        # 更新 knowledge_foundation
        dimensions = evaluation.get("dimensions") or {}
        kf = KnowledgeFoundation()
        if existing_knowledge:
            for key in ["python", "linear_algebra", "calculus", "machine_learning", "deep_learning"]:
                setattr(kf, key, existing_knowledge.get(key, getattr(kf, key)))
        if dimensions:
            mastery = dimensions.get("knowledge_mastery", kf.machine_learning)
            kf.machine_learning = max(kf.machine_learning, int(mastery) if mastery else kf.machine_learning)

        fallback_profile = CourseProfile(
            user_id=context.user_id,
            course_id=context.course_id,
            version=cp.get("version", 0) + 1,
            knowledge_foundation=kf,
            learning_goal=cp.get("learning_goal", ""),
            cognitive_style=cp.get("cognitive_style", "案例驱动型"),
            preferred_resources=cp.get("preferred_resources") or ["mindmap", "exercise", "document"],
            weak_points=[WeakPoint(**wp) if isinstance(wp, dict) else wp for wp in new_weak_points],
            interest_directions=cp.get("interest_directions") or [],
            update_reason="rule_based_evaluation_update",
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

        return ProfileOutput(
            profile=fallback_profile,
            completeness=cp.get("completeness", 0.3) if isinstance(cp, dict) else 0.3,
            confidence=0.4,
            sources=["rule_based_evaluation_update"],
            next_questions=[],
            can_start_journey=False,
        )

    # ---- 流式：供 /api/profile/chat SSE 端点使用 ----

    async def chat(
        self,
        student_id: str,
        message: str,
        history: Optional[List[str]] = None,
        current_profile: Optional[Dict] = None,
        context: Optional[AgentContext] = None,
    ) -> AsyncIterator[str]:
        """
        对话式画像构建（流式，SSE 事件）。

        产出以下类型的 SSE 事件：
        - data: {"type":"chat","content":"..."}   自然语言回复
        - data: {"type":"profile_update","profile":{...}}  画像更新
        - data: {"type":"done"}

        Args:
            student_id: 学生标识
            message: 当前用户消息
            history: 历史对话消息
            current_profile: 已有画像
            context: 可选 AgentContext；未提供时自动从 student_id 构造
        """
<<<<<<< Updated upstream
=======
        if context is None:
            course_id = "default"
            if current_profile:
                cp = current_profile.get("profile", current_profile)
                course_id = cp.get("course_id", "default") if isinstance(cp, dict) else "default"
            context = AgentContext(user_id=student_id, course_id=course_id)
        logger.info(
            "[ProfileAgent] chat user_id=%s course_id=%s",
            context.user_id, context.course_id,
        )

        try:
            from safety.content_filter import check_safety
        except ModuleNotFoundError:
            from backend.safety.content_filter import check_safety

        filter_result = check_safety(message, context="profile_message")
        if not filter_result["safe"]:
            reply = filter_result.get("reason") or "该内容无法用于学习画像，请重新描述你的学习情况。"
            yield f'data: {{"type":"chat","content":{json.dumps(reply, ensure_ascii=False)}}}\n\n'
            yield f'data: {{"type":"done"}}\n\n'
            return

>>>>>>> Stashed changes
        user_prompt = self._build_user_prompt(message, history, current_profile)

        full_response = []
        try:
            async for chunk in self.call_llm(user_prompt):
                full_response.append(chunk)
        except Exception as e:
            # 降级
            result = self._keyword_fallback(student_id, message, history or [])
            reply = self._build_chat_reply(result)
            yield f'data: {{"type":"chat","content":{json.dumps(reply, ensure_ascii=False)}}}\n\n'
            profile_json = json.dumps(result, ensure_ascii=False)
            yield f'data: {{"type":"profile_update","profile":{profile_json}}}\n\n'
            yield f'data: {{"type":"done"}}\n\n'
            return

        raw = "".join(full_response)
        parsed = self._parse_llm_json(raw)
        if parsed:
            result = {
                "student_id": student_id,
                "profile": parsed.get("profile", {}),
                "completeness": parsed.get("completeness", 0.3),
                "confidence": parsed.get("confidence", 0.5),
                "sources": parsed.get("sources", ["dialogue"]),
                "next_questions": parsed.get("next_questions", []),
            }
            if "learning_history" not in result["profile"]:
                result["profile"]["learning_history"] = history or []
            reply = parsed.get("reply") or parsed.get("chat_reply") or self._build_chat_reply(result)
            yield f'data: {{"type":"chat","content":{json.dumps(reply, ensure_ascii=False)}}}\n\n'
            profile_json = json.dumps(result, ensure_ascii=False)
            yield f'data: {{"type":"profile_update","profile":{profile_json}}}\n\n'
        else:
            # 解析失败，用 fallback
            result = self._keyword_fallback(student_id, message, history or [])
            reply = self._build_chat_reply(result)
            yield f'data: {{"type":"chat","content":{json.dumps(reply, ensure_ascii=False)}}}\n\n'
            profile_json = json.dumps(result, ensure_ascii=False)
            yield f'data: {{"type":"profile_update","profile":{profile_json}}}\n\n'

        yield f'data: {{"type":"done"}}\n\n'

    # ---- 内部工具方法 ----

    def _build_user_prompt(
        self,
        message: str,
        history: Optional[List[str]] = None,
        current_profile: Optional[Dict] = None,
    ) -> str:
        """构造发给 LLM 的 user prompt"""
        parts = []

        parts.append("## 学生当前对话")
        parts.append(message)

        if history:
            parts.append("\n## 历史学习记录")
            for i, h in enumerate(history, 1):
                parts.append(f"{i}. {h}")

        if current_profile:
            parts.append("\n## 已有画像（增量更新）")
            parts.append("请基于以下已有画像，结合本次对话进行增量更新：")
            parts.append("```json")
            parts.append(json.dumps(current_profile, ensure_ascii=False, indent=2))
            parts.append("```")

        parts.append("\n请提取学生画像，只输出 JSON。")
        return "\n".join(parts)

    def _parse_llm_json(self, text: str) -> Optional[Dict]:
        """
        从 LLM 输出中提取 JSON 对象。

        处理常见情况：
        - 纯 JSON
        - JSON 被 ```json ... ``` 包裹
        - 前后有额外文本
        """
        if not text or not text.strip():
            return None

        text = text.strip()

        # 尝试 1：提取 ```json ... ``` 代码块
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if m:
            text = m.group(1).strip()

        # 尝试 2：找到第一个 { 和最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        text = text[start:end + 1]

        # 尝试解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试 3：修复常见 JSON 错误（尾部逗号等）
            try:
                cleaned = re.sub(r",\s*([}\]])", r"\1", text)
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return None

    def _build_chat_reply(self, result: Dict) -> str:
        """Build user-facing text from structured profile output."""
        profile = result.get("profile", {}) if isinstance(result, dict) else {}
        next_questions = result.get("next_questions", []) if isinstance(result, dict) else []
        completeness = result.get("completeness", 0) if isinstance(result, dict) else 0

        lines = ["我已经根据你的描述更新了学习画像。"]

        knowledge_level = profile.get("knowledge_level")
        learning_goal = profile.get("learning_goal")
        cognitive_style = profile.get("cognitive_style")
        weaknesses = profile.get("weakness") or []
        interests = profile.get("interest") or []
        pace_preference = profile.get("pace_preference")

        summary = []
        if knowledge_level:
            summary.append(f"当前基础：{knowledge_level}")
        if learning_goal:
            summary.append(f"学习目标：{learning_goal}")
        if cognitive_style:
            summary.append(f"学习偏好：{cognitive_style}")
        if weaknesses:
            summary.append(f"需要重点补强：{', '.join(weaknesses)}")
        if interests:
            summary.append(f"兴趣方向：{', '.join(interests)}")
        if pace_preference:
            summary.append(f"学习节奏：{pace_preference}")

        if summary:
            lines.append("")
            lines.extend(f"- {item}" for item in summary)

        if completeness and completeness < 0.7 and next_questions:
            lines.append("")
            lines.append("为了继续完善画像，我还想确认：")
            lines.extend(f"{idx}. {question}" for idx, question in enumerate(next_questions[:3], 1))

        return "\n".join(lines)

    def _keyword_fallback(
        self,
        student_id: str,
        message: str,
        history: List[str],
    ) -> Dict:
        """
        关键字规则降级方案 —— LLM 不可用时的兜底逻辑。

        保留 v0 的简单关键字匹配，保证基本可用性。
        """
        knowledge_level = "中级"
        learning_goal = "掌握课程核心概念"
        cognitive_style = "偏好图解与案例"
        weaknesses: List[str] = []
        interests: List[str] = []
        pace_preference = "中速均衡型"

        msg = message.lower()

        if "入门" in msg or "基础" in msg or "零基础" in msg:
            knowledge_level = "初级"
            learning_goal = "掌握基础概念与示例"
        if "高级" in msg or "进阶" in msg or "深入" in msg:
            knowledge_level = "中高级"
        if "项目" in msg or "实践" in msg or "动手" in msg:
            learning_goal = "完成实践项目"
            cognitive_style = "偏好动手和代码示例"
        if "数学" in msg or "推导" in msg or "公式" in msg:
            weaknesses.append("数学推导")
        if "概率" in msg or "统计" in msg:
            weaknesses.append("概率与统计")
        if "代码" in msg or "编程" in msg:
            interests.append("代码案例")
        if "视频" in msg or "看" in msg:
            cognitive_style = "视觉型（偏好视频/图解）"
        if "快" in msg or "速成" in msg:
            pace_preference = "快速概览型"
        if "慢" in msg or "仔细" in msg:
            pace_preference = "慢速深入型"

        return {
            "student_id": student_id,
            "profile": {
                "knowledge_level": knowledge_level,
                "learning_goal": learning_goal,
                "learning_history": history,
                "cognitive_style": cognitive_style,
                "weakness": weaknesses,
                "interest": interests,
                "pace_preference": pace_preference,
            },
            "completeness": 0.5 if (weaknesses or interests) else 0.3,
            "confidence": 0.4,  # 规则匹配置信度低
            "sources": ["keyword_fallback"],
<<<<<<< Updated upstream
            "next_questions": [
                "你希望通过本课程达到什么目标？",
                "你更偏好视频、图文还是动手代码示例？",
                "你在学习中最容易卡住的地方是什么？",
            ],
        }
=======
            "next_questions": next_questions,
        })

    def _legacy_dict_to_profile_output(
        self,
        context: AgentContext,
        data: dict,
    ) -> ProfileOutput:
        """
        将旧版 _keyword_fallback 返回的 dict 转换为 ProfileOutput Pydantic 模型。

        旧 dict 格式 → 新 CourseProfile 映射：
        - knowledge_level → 无直接对应，体现在 learning_goal 描述中
        - weakness (list[str]) → weak_points (list[WeakPoint])
        - interest (list[str]) → interest_directions (list[str])
        """
        profile_data = data.get("profile", {}) if isinstance(data, dict) else {}
        if not isinstance(profile_data, dict):
            profile_data = {}

        # 转换 old weakness strings → WeakPoint objects
        old_weakness = profile_data.get("weakness") or []
        weak_points = [
            WeakPoint(
                knowledge_point_id=f"kp_legacy_{i}",
                name=w,
                score=50,
            )
            for i, w in enumerate(old_weakness) if w
        ]

        # 转换 old interest strings → interest_directions
        interest_directions = list(profile_data.get("interest") or [])

        # 构造 learning_goal（融入 knowledge_level 信息）
        knowledge_level = profile_data.get("knowledge_level", "")
        learning_goal = profile_data.get("learning_goal", "")
        if knowledge_level and knowledge_level not in learning_goal:
            learning_goal = f"[{knowledge_level}] {learning_goal}".strip()

        course_profile = CourseProfile(
            user_id=context.user_id,
            course_id=context.course_id,
            version=1,
            knowledge_foundation=KnowledgeFoundation(),
            learning_goal=learning_goal,
            cognitive_style=profile_data.get("cognitive_style", "案例驱动型"),
            preferred_resources=["mindmap", "exercise", "document"],
            weak_points=weak_points,
            interest_directions=interest_directions,
            update_reason="keyword_fallback",
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

        completeness = data.get("completeness", 0.0)
        return ProfileOutput(
            profile=course_profile,
            completeness=max(0.0, min(1.0, float(completeness))),
            confidence=data.get("confidence", 0.4),
            sources=data.get("sources", ["keyword_fallback"]),
            next_questions=data.get("next_questions") or [],
            can_start_journey=completeness >= PROFILE_READY_THRESHOLD,
        )

    @staticmethod
    def _finalize_result(result: Dict) -> Dict:
        """Clamp readiness fields so every ProfileAgent path follows one contract."""
        try:
            completeness = max(0.0, min(1.0, float(result.get("completeness", 0.0))))
        except (TypeError, ValueError):
            completeness = 0.0
        result["completeness"] = completeness
        result["can_start_journey"] = completeness >= PROFILE_READY_THRESHOLD
        if result["can_start_journey"]:
            result["next_questions"] = []
        return result

    @staticmethod
    def _calc_completeness(
        knowledge_level: str,
        learning_goal: str,
        cognitive_style: str,
        weaknesses: List[str],
        interests: List[str],
        pace_preference: str,
    ) -> float:
        """基于各维度信息覆盖情况计算 completeness (0.0~1.0)。

        评分逻辑（关键字降级路径偏保守，LLM 路径由模型自行判定）：
        - knowledge_level: 非默认（非"中级"）= +0.15
        - learning_goal: 非默认（非"掌握课程核心概念"）= +0.20
        - cognitive_style: 非默认（非"偏好图解与案例"）= +0.12
        - weakness: 有内容 = +0.10
        - interest: 有内容 = +0.10
        - pace_preference: 非默认（非"中速均衡型"）= +0.08
        上限 0.90；六个维度通过多轮对话补齐后，降级路径也能达到 0.85 解锁线。
        """
        score = 0.15  # base: 至少有一定信息

        if knowledge_level and knowledge_level != "中级":
            score += 0.15
        if learning_goal and learning_goal != "掌握课程核心概念":
            score += 0.20
        if cognitive_style and cognitive_style != "偏好图解与案例":
            score += 0.12
        if weaknesses:
            score += 0.10
        if interests:
            score += 0.10
        if pace_preference and pace_preference != "中速均衡型":
            score += 0.08

        return min(score, 0.90)

    @staticmethod
    def _gen_next_questions(
        knowledge_level: str,
        learning_goal: str,
        cognitive_style: str,
        weaknesses: List[str],
        interests: List[str],
        pace_preference: str,
    ) -> List[str]:
        """生成追问列表：优先询问最缺的维度，最多 2 条。

        优先级：薄弱点 > 学习目标 > 认知风格 > 兴趣 > 学习节奏
        不重复询问已有明确信息的维度。
        """
        questions: List[str] = []

        # 1. 薄弱点 — 最高优先级
        if not weaknesses:
            questions.append("你在学习中最容易卡住的地方是什么？（比如数学推导、代码实现等）")

        # 2. 学习目标
        if len(questions) < 2 and (not learning_goal or learning_goal == "掌握课程核心概念"):
            questions.append("你希望通过本课程达到什么具体目标？（比如掌握某个算法、完成一个项目等）")

        # 3. 认知风格
        if len(questions) < 2 and (
            not cognitive_style or cognitive_style == "偏好图解与案例"
        ):
            questions.append("你更偏好哪种学习方式？视频讲解、图文教程还是动手代码示例？")

        # 4. 兴趣方向
        if len(questions) < 2 and not interests:
            questions.append("你对哪些技术方向或应用领域比较感兴趣？")

        # 5. 知识水平
        if len(questions) < 2 and (not knowledge_level or knowledge_level == "中级"):
            questions.append("你目前的基础大概在什么水平？零基础/入门/中级/进阶？")

        # 6. 学习节奏
        if len(questions) < 2 and (
            not pace_preference or pace_preference == "中速均衡型"
        ):
            questions.append("你偏好快节奏速成还是慢节奏深入的学习方式？")

        return questions[:2]
>>>>>>> Stashed changes
