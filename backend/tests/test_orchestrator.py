"""Orchestrator 闭环测试。"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_context import AgentContext
from core.errors import CourseContextMissing


class TestOrchestratorFlows:
    """测试 Orchestrator 核心流程需要 course_id。"""

    def test_context_missing_course_id(self):
        """初始化学习时缺少 course_id 应报错。"""
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()

        ctx = AgentContext(user_id="u1", course_id="")  # 空字符串

        import asyncio
        with pytest.raises(CourseContextMissing):
            asyncio.run(orch.initialize_course_learning(context=ctx, message="test"))

    def test_tutor_chat_missing_course_id(self):
        """Tutor 问答缺少 course_id 应报错。"""
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()

        ctx = AgentContext(user_id="u1", course_id="")

        import asyncio
        with pytest.raises(CourseContextMissing):
            asyncio.run(orch.tutor_chat(context=ctx, question="test"))

    def test_context_with_course_id_valid(self):
        """有 course_id 的上下文不应报错（但无 Agent 注册时会跳过）。"""
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()

        ctx = AgentContext(
            user_id="u1",
            course_id="ai_deep_learning_demo",
        )

        # 没有注册 Agent 时不应崩溃，但结果可能为空
        import asyncio
        result = asyncio.run(orch.initialize_course_learning(context=ctx))
        assert "orchestration_trace" in result


class TestOrchestratorClosedLoop:
    """测试评估→路径调整→画像更新的闭环。"""

    def test_process_assessment_requires_course(self):
        """处理测评必须绑定 course_id。"""
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()

        ctx = AgentContext(user_id="u1", course_id="")

        import asyncio
        with pytest.raises(CourseContextMissing):
            asyncio.run(orch.process_stage_assessment(
                context=ctx,
                assessment_result={},
            ))

    def test_apply_adjustment_requires_course(self):
        """应用路径调整必须绑定 course_id。"""
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()

        ctx = AgentContext(user_id="u1", course_id="")

        import asyncio
        with pytest.raises(CourseContextMissing):
            asyncio.run(orch.apply_evaluation_adjustment(
                context=ctx,
                evaluation_id="eval_001",
            ))

    def test_closed_loop_flow(self):
        """模拟完整闭环：评估 → 调整预览 → 确认应用。"""
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()

        ctx = AgentContext(
            user_id="demo_student",
            course_id="ai_deep_learning_demo",
            stage_id="stage_gradient_descent",
        )

        import asyncio

        # Flow 4: process_stage_assessment
        # 无 Agent 注册时不应崩溃
        result = asyncio.run(orch.process_stage_assessment(
            context=ctx,
            assessment_result={"score": 72},
            records=[],
            profile={},
            current_path={"current_stage": 2},
        ))
        assert "orchestration_trace" in result

        # Flow 5: apply adjustment
        result2 = asyncio.run(orch.apply_evaluation_adjustment(
            context=ctx,
            evaluation_id="eval_001",
        ))
        assert "orchestration_trace" in result2
