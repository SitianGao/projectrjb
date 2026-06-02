"""
knowledge_agent.py
功能：提供课程知识检索
"""

from typing import Dict

class KnowledgeAgent:

    def __init__(self):
        self.knowledge_base = {
            "AI": "人工智能基础包括机器学习、深度学习等",
            "DS": "数据结构包括数组、链表、树、图"
        }

    def search(self, key: str) -> str:
        return self.knowledge_base.get(key, "暂无相关知识")


if __name__ == "__main__":
    agent = KnowledgeAgent()
    print(agent.search("AI"))