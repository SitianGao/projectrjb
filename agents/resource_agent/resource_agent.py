"""
resource_agent.py
功能：生成学习资源（文档/题目/案例）
"""

from typing import Dict

class ResourceAgent:

    def generate_resources(self, topic: str) -> Dict:

        return {
            "document": f"{topic} - 知识讲解文档",
            "mind_map": f"{topic} - 思维导图结构",
            "exercises": [
                f"{topic} 基础题",
                f"{topic} 提升题",
                f"{topic} 综合题"
            ],
            "case": f"{topic} 编程实践案例"
        }


if __name__ == "__main__":
    agent = ResourceAgent()
    print(agent.generate_resources("数据结构"))