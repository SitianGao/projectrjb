"""
ProfileAgent v01 —— 基于 LLM 的学生画像构建智能体

职责：
- 通过自然语言对话提取学生画像（6+ 维度）
- 支持增量更新（多轮对话画像逐步完善）
- 提供非流式 build_profile() 供编排器使用
- 提供流式 chat() 供 SSE 端点使用

设计依据：docs/ai/agent-io.md §5 + docs/requirement.md §2.1(1)
"""
import json
import re
from typing import AsyncIterator, Optional, List, Dict

from .base_agent import BaseAgent


class ProfileAgent(BaseAgent):
    """学生画像构建智能体 —— LLM prompt v01"""

    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.name = "ProfileAgent"

    def get_system_prompt(self) -> str:
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
        )

    # ---- 非流式：供编排器 pipeline 使用 ----

    async def build_profile(
        self,
        student_id: str,
        message: str,
        history: Optional[List[str]] = None,
        current_profile: Optional[Dict] = None,
    ) -> Dict:
        """
        构建/更新学生画像（非流式，返回完整 dict）。

        Args:
            student_id: 学生唯一标识
            message: 当前轮用户消息
            history: 历史对话消息列表
            current_profile: 已有画像（增量更新时传入）

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

    # ---- 流式：供 /api/profile/chat SSE 端点使用 ----

    async def chat(
        self,
        student_id: str,
        message: str,
        history: Optional[List[str]] = None,
        current_profile: Optional[Dict] = None,
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
        """
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
            "next_questions": [
                "你希望通过本课程达到什么目标？",
                "你更偏好视频、图文还是动手代码示例？",
                "你在学习中最容易卡住的地方是什么？",
            ],
        }
