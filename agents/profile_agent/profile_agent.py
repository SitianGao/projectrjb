"""
profile_agent.py
功能：通过对话构建学生学习画像
"""

from typing import Dict

class ProfileAgent:

    def __init__(self, student_id: str):
        self.student_id = student_id
        self.profile: Dict = {
            "knowledge_level": "unknown",
            "goal": "",
            "learning_style": "",
            "weakness": "",
            "speed": "",
            "interest": ""
        }

    def update_profile(self, info: Dict):
        """
        更新学生画像（对话驱动）
        """
        for k, v in info.items():
            if k in self.profile:
                self.profile[k] = v

    def get_profile(self):
        return self.profile


if __name__ == "__main__":
    agent = ProfileAgent("stu001")
    agent.update_profile({
        "knowledge_level": "beginner",
        "goal": "learn AI",
        "learning_style": "visual"
    })
    print(agent.get_profile())