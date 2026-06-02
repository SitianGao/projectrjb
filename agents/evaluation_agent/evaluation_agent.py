"""
evaluation_agent.py
功能：学习效果评估 + 多智能体协作反馈
"""

from typing import List, Dict, Any
import datetime

class EvaluationAgent:

    def __init__(self, student_id: str):
        self.student_id = student_id
        self.records: List[Dict[str, Any]] = []
        self.learning_path: List[str] = []

    def add_record(self, resource: str, score: float = None):
        self.records.append({
            "resource": resource,
            "score": score,
            "time": datetime.datetime.now()
        })

    def update_path(self, path: List[str]):
        self.learning_path = path

    def evaluate(self):

        if not self.records:
            return {"status": "no data"}

        scores = [r["score"] for r in self.records if r["score"] is not None]

        avg = sum(scores) / len(scores) if scores else 0

        completion = len(self.records) / max(len(self.learning_path), 1) * 100

        return {
            "average_score": round(avg, 2),
            "completion_rate": round(min(completion, 100), 2)
        }

    def feedback(self):

        result = self.evaluate()

        advice = []

        if result.get("average_score", 0) < 60:
            advice.append("需要加强基础知识")

        if result.get("completion_rate", 0) < 70:
            advice.append("学习进度偏慢")

        return {
            "result": result,
            "advice": advice
        }


if __name__ == "__main__":
    agent = EvaluationAgent("stu001")
    agent.add_record("AI基础", 80)
    agent.add_record("数据结构", 50)
    print(agent.feedback())