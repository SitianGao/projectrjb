"""
planner_agent.py
功能：根据学生画像生成学习路径
"""

from typing import List, Dict

class PlannerAgent:

    def __init__(self):
        pass

    def generate_path(self, profile: Dict) -> List[str]:
        """
        根据学生情况生成学习路径
        """

        base_path = [
            "基础概念学习",
            "核心知识理解",
            "案例练习",
            "综合项目实践"
        ]

        if profile.get("knowledge_level") == "beginner":
            return base_path

        if profile.get("knowledge_level") == "advanced":
            return [
                "快速复习基础",
                "高级算法学习",
                "项目优化",
                "论文阅读"
            ]

        return base_path


if __name__ == "__main__":
    agent = PlannerAgent()
    print(agent.generate_path({"knowledge_level": "beginner"}))