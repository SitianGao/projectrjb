# backend/agents/profile_agent.py
import json
from typing import Optional, List, Dict

# 如果仓库已有 BaseAgent，请改为 from .base import BaseAgent
# 下面提供一个轻量的 BaseAgent 兼容体（若仓库已有可删除）
class BaseAgent:
    def __init__(self, name: str = "BaseAgent"):
        self.name = name

class ProfileAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ProfileAgent")

    def get_system_prompt(self) -> str:
        return (
            "你是学生画像构建智能体。"
            "通过用户的对话与历史学习记录，提取学生的知识水平、学习目标、认知风格、易错点与兴趣等信息，"
            "输出固定的 JSON 结构，保证字段完整且可解析。"
        )

    def build_profile(
        self,
        student_id: str,
        message: str,
        history: Optional[List[str]] = None,
        current_profile: Optional[Dict] = None
    ) -> str:
        """
        简单规则化实现：基于输入 message 提取若干字段（可后续替换为大模型解析）
        返回 JSON 字符串（utf-8，不转义中文）
        """
        history = history or []
        # 极简解析示例（真实场景用 NER/LLM 提取）
        knowledge_level = "中级"
        learning_goal = "掌握课程核心概念"
        cognitive_style = "偏好图解与案例"
        weaknesses = []
        interests = []

        # 简单关键字判断示例
        msg = message.lower()
        if "入门" in msg or "基础" in msg:
            knowledge_level = "初级"
            learning_goal = "掌握基础概念与示例"
        if "项目" in msg or "实践" in msg:
            learning_goal = "完成实践项目"
            cognitive_style = "偏好动手和代码示例"
        if "数学" in msg or "推导" in msg:
            weaknesses.append("数学推导")
        if "代码" in msg:
            interests.append("代码案例")

        profile = {
            "student_id": student_id,
            "profile": {
                "knowledge_level": knowledge_level,
                "learning_goal": learning_goal,
                "learning_history": history,
                "cognitive_style": cognitive_style,
                "weakness": weaknesses,
                "interest": interests
            },
            "completeness": 0.6,
            "next_questions": [
                "你希望通过本课程达到什么目标？",
                "你更偏好视频、图文还是动手代码示例？"
            ]
        }

        return json.dumps(profile, ensure_ascii=False, indent=2)
