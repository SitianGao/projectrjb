"""
agent_orchestrator.py
功能：多智能体调度中心（核心控制器）

作用：
    1. 统一管理所有智能体
    2. 控制数据流（学生 → 画像 → 规划 → 资源 → 评估）
    3. 对外提供一个统一接口（比赛重点）
"""

from agents.profile_agent.profile_agent import ProfileAgent
from agents.planner_agent.planner_agent import PlannerAgent
from agents.resource_agent.resource_agent import ResourceAgent
from agents.knowledge_agent.knowledge_agent import KnowledgeAgent
from agents.evaluation_agent.evaluation_agent import EvaluationAgent


class AgentOrchestrator:

    def __init__(self, student_id: str):

        self.student_id = student_id

        # 初始化所有智能体
        self.profile_agent = ProfileAgent(student_id)
        self.planner_agent = PlannerAgent()
        self.resource_agent = ResourceAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.evaluation_agent = EvaluationAgent(student_id)

    # =========================
    # Step 1：构建学生画像
    # =========================
    def build_profile(self, user_input: dict):
        """
        user_input: 来自用户对话的信息
        """
        self.profile_agent.update_profile(user_input)
        return self.profile_agent.get_profile()

    # =========================
    # Step 2：生成学习路径
    # =========================
    def create_learning_path(self):

        profile = self.profile_agent.get_profile()
        path = self.planner_agent.generate_path(profile)

        # 交给评估器记录路径
        self.evaluation_agent.update_path(path)

        return path

    # =========================
    # Step 3：生成学习资源
    # =========================
    def generate_resources(self, topic: str):

        resources = self.resource_agent.generate_resources(topic)

        return resources

    # =========================
    # Step 4：知识查询
    # =========================
    def query_knowledge(self, key: str):

        return self.knowledge_agent.search(key)

    # =========================
    # Step 5：学习记录 + 评估
    # =========================
    def record_learning(self, resource: str, score: float = None):

        self.evaluation_agent.add_record(resource, score)

    def evaluate(self):

        return self.evaluation_agent.feedback()

    # =========================
    # ⭐ 一键完整流程（比赛展示重点）
    # =========================
    def run_full_pipeline(self, user_input: dict, topic: str):

        print("=== Step 1: 构建画像 ===")
        profile = self.build_profile(user_input)

        print("=== Step 2: 生成路径 ===")
        path = self.create_learning_path()

        print("=== Step 3: 生成资源 ===")
        resources = self.generate_resources(topic)

        print("=== Step 4: 知识查询 ===")
        knowledge = self.query_knowledge(topic)

        return {
            "profile": profile,
            "learning_path": path,
            "resources": resources,
            "knowledge": knowledge
        }


# =========================
# 示例运行（非常重要，用于演示）
# =========================
if __name__ == "__main__":

    orchestrator = AgentOrchestrator("stu001")

    result = orchestrator.run_full_pipeline(
        user_input={
            "knowledge_level": "beginner",
            "goal": "learn AI",
            "learning_style": "visual"
        },
        topic="AI"
    )

    print("\n=== FINAL OUTPUT ===")
    print(result)

    # 模拟学习评估
    orchestrator.record_learning("AI基础文档", 80)
    orchestrator.record_learning("AI练习题", 60)

    print("\n=== EVALUATION ===")
    print(orchestrator.evaluate())