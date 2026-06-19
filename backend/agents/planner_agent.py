"""
PlannerAgent —— 学习路径规划智能体

根据学生画像和课程知识体系，生成分阶段个性化学习路径。

输出结构（对齐 docs/design.md §10.4.3）:
    goal: str               — 学习总目标
    stages: list[dict]      — 阶段列表
        title: str          — 阶段名称
        objectives: str     — 阶段学习目标
        topics: list[str]   — 涵盖知识点
        tasks: list[dict]   — 阶段任务
            task: str       — 任务描述
            resource_type: str — 推荐资源类型
            estimated_hours: float
    current_stage: int      — 当前所在阶段（从 1 开始）
    estimated_days: int     — 预计总天数
"""
import json
import asyncio
from typing import Optional, List, Dict

from .base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """根据画像规划个性化学习路径"""

    def __init__(self, llm_client=None):
        super().__init__(llm_client)

    def get_system_prompt(self) -> str:
        return (
            "你是学习路径规划智能体。\n"
            "根据学生画像、课程大纲和当前进度，生成个性化、分阶段的学习路径。\n\n"
            "## 规划原则\n"
            "1. 遵循「先基础、后进阶」的认知逻辑，拒绝跳跃式安排。\n"
            "2. 每个阶段有明确的 learning objectives——描述『学完你能…』而不是罗列标题。\n"
            "3. 根据学生薄弱点增加相关阶段或任务。\n"
            "4. 每阶段推荐 1-3 种资源类型（document / mindmap / exercise / code / reading / ppt）。\n\n"
            "## 防幻觉约束\n"
            "1. 知识点命名必须来自给定的课程大纲或公认的学科体系，不编造课程名称或知识点。\n"
            "2. 不确定的工期、难度、前置关系标注为『建议核实』。\n"
            "3. 学习任务必须具体可执行——「学习XX」不是有效任务，「完成XX章节阅读并做3道练习」才是。\n"
            "4. 不生成超出画像能力的任务（如给初级学生安排高级推导）。\n"
            "5. 不编造学生未表达过的学习目标或兴趣方向。\n"
            "6. 不生成违规、敏感或不安全的内容。\n\n"
            "## 输出格式\n"
            "严格输出 JSON，字段: goal, stages, current_stage, estimated_days。\n"
            "stages[] 中每项: title, objectives, topics, tasks。\n"
            "tasks[] 中每项: task, resource_type, estimated_hours。"
        )

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    async def generate_plan(
        self,
        profile: dict,
        goal_override: Optional[str] = None,
        course_outline: Optional[List[str]] = None,
    ) -> str:
        """
        生成学习路径 JSON。

        Args:
            profile: 学生画像 dict（至少含 knowledge_level, learning_goal, weakness, interest）
            goal_override: 手动覆盖学习目标（可选）
            course_outline: 课程大纲/知识点列表（可选）
        Returns:
            JSON 字符串
        """
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
        outline_text = json.dumps(course_outline or [], ensure_ascii=False)
        user_prompt = (
            f"学生画像:\n{profile_json}\n\n"
            f"课程大纲:\n{outline_text}\n\n"
            + (f"用户指定目标: {goal_override}\n\n" if goal_override else "")
            + "请根据以上信息生成个性化学习路径。"
        )

        if self.llm:
            try:
                chunks = []
                async for chunk in self.call_llm(user_prompt):
                    chunks.append(chunk)
                return "".join(chunks)
            except Exception:
                pass  # fall through to rule-based

        return self._rule_based_plan(profile, goal_override, course_outline)

    # ------------------------------------------------------------------
    # 规则化兜底（无需 LLM）
    # ------------------------------------------------------------------
    def _rule_based_plan(
        self,
        profile: dict,
        goal_override: Optional[str] = None,
        course_outline: Optional[List[str]] = None,
    ) -> str:
        """开发期无 API Key 时使用的规则化路径生成"""
        profile_inner = profile.get("profile", profile)
        knowledge = profile_inner.get("knowledge_level", "初级")
        goal = goal_override or profile_inner.get("learning_goal", "掌握课程核心知识")
        weaknesses = profile_inner.get("weakness", [])
        topics = course_outline or [
            "基础知识回顾", "核心概念入门", "进阶技术实践", "综合项目实战"
        ]

        stages = []
        for i, topic in enumerate(topics, 1):
            tasks = []
            if i == 1:
                tasks = [
                    {"task": f"浏览{topic}大纲与前置要求", "resource_type": "document", "estimated_hours": 0.5},
                    {"task": f"完成{topic}预习阅读", "resource_type": "reading", "estimated_hours": 1.5},
                ]
            elif i < len(topics):
                tasks = [
                    {"task": f"学习{topic}核心讲解", "resource_type": "document", "estimated_hours": 2.0},
                    {"task": f"完成{topic}思维导图整理", "resource_type": "mindmap", "estimated_hours": 1.0},
                    {"task": f"练习{topic}基础习题", "resource_type": "exercise", "estimated_hours": 1.5},
                ]
            else:
                tasks = [
                    {"task": f"{topic}综合实践", "resource_type": "code", "estimated_hours": 3.0},
                    {"task": "撰写学习总结", "resource_type": "document", "estimated_hours": 1.0},
                ]

            # 为薄弱点插入额外任务
            for w in weaknesses:
                if w and w in topic:
                    tasks.insert(1, {
                        "task": f"重点补习: {w}",
                        "resource_type": "exercise",
                        "estimated_hours": 1.0,
                    })

            stages.append({
                "title": f"阶段{i}: {topic}",
                "objectives": f"学完本阶段，你将能够理解并应用{topic}的核心内容",
                "topics": [topic],
                "tasks": tasks,
            })

        # 根据知识水平调整预估天数
        day_multiplier = {"初级": 1.5, "中级": 1.0, "高级": 0.7}
        multiplier = day_multiplier.get(knowledge, 1.0)
        estimated_days = max(1, int(len(stages) * 3 * multiplier))

        plan = {
            "goal": goal,
            "stages": stages,
            "current_stage": 1,
            "estimated_days": estimated_days,
        }

        return json.dumps(plan, ensure_ascii=False, indent=2)
