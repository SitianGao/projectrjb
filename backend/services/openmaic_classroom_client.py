"""OpenMAIC 在线课堂 Adapter。

外部 OpenMAIC 服务可用时走 HTTP；不可用时返回本地结构化课堂，保证主后端
和比赛演示流程不被外部服务拖垮。
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any


OPENMAIC_CLASSROOM_SERVICE_URL = os.getenv(
    "OPENMAIC_CLASSROOM_SERVICE_URL",
    "http://openmaic-classroom:3200",
)


class OpenMaicClassroomClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or OPENMAIC_CLASSROOM_SERVICE_URL).rstrip("/")

    async def generate_classroom(self, brief: dict[str, Any]) -> dict[str, Any]:
        """生成课堂结构。外部服务失败时降级为本地默认课堂。"""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=12) as client:
                resp = await client.post(f"{self.base_url}/api/classrooms/generate", json=brief)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict) and data.get("scenes"):
                    return data
        except Exception:
            pass
        return build_gradient_descent_classroom(brief, source="local_adapter")


def build_gradient_descent_classroom(brief: dict[str, Any], source: str = "local_adapter") -> dict[str, Any]:
    classroom_id = brief.get("classroom_id") or "classroom_gradient_001"
    now = datetime.datetime.utcnow().isoformat()
    kp_ids = brief.get("knowledge_point_ids") or [
        "kp_gradient",
        "kp_learning_rate",
        "kp_convergence",
    ]
    goal_ids = brief.get("learning_goal_ids") or ["goal_gradient_update", "goal_learning_rate"]
    scenes = [
        {
            "scene_id": "scene_intro",
            "order": 1,
            "title": "课程导入",
            "scene_type": "introduction",
            "estimated_minutes": 3,
            "required": True,
            "knowledge_point_ids": ["kp_loss_function"],
            "learning_goal_ids": goal_ids,
            "content": {
                "question": "为什么机器学习模型需要不断调整参数？",
                "goal_cards": ["理解参数更新", "观察损失下降", "判断学习率影响"],
            },
            "source_ids": brief.get("references", []),
            "confidence": 0.92,
            "validation_status": "validated",
        },
        {
            "scene_id": "scene_loss_gradient",
            "order": 2,
            "title": "损失函数与梯度",
            "scene_type": "presentation",
            "estimated_minutes": 4,
            "required": True,
            "knowledge_point_ids": ["kp_loss_function", "kp_gradient"],
            "learning_goal_ids": ["goal_gradient_update"],
            "content": {
                "slides": [
                    {"title": "损失函数", "body": "损失函数衡量模型预测和真实结果之间的差距。"},
                    {"title": "梯度方向", "body": "梯度指向函数上升最快方向，负梯度用于降低损失。"},
                ],
            },
            "source_ids": brief.get("references", []),
            "confidence": 0.9,
            "validation_status": "validated",
        },
        {
            "scene_id": "scene_whiteboard_update",
            "order": 3,
            "title": "参数更新白板演示",
            "scene_type": "whiteboard",
            "estimated_minutes": 4,
            "required": True,
            "knowledge_point_ids": ["kp_gradient"],
            "learning_goal_ids": ["goal_gradient_update"],
            "content": {
                "formula": "w = w - learning_rate * gradient",
                "steps": ["计算当前损失", "求损失对参数的梯度", "沿负梯度方向移动", "重复直到收敛"],
            },
            "source_ids": brief.get("references", []),
            "confidence": 0.91,
            "validation_status": "validated",
        },
        {
            "scene_id": "scene_learning_rate_simulation",
            "order": 4,
            "title": "学习率交互模拟",
            "scene_type": "simulation",
            "estimated_minutes": 5,
            "required": True,
            "knowledge_point_ids": ["kp_learning_rate", "kp_convergence"],
            "learning_goal_ids": ["goal_learning_rate"],
            "content": {
                "preset_learning_rates": [0.001, 0.01, 0.1, 1.0, 2.0],
                "prompt": "调整学习率，观察损失曲线如何变化。",
            },
            "source_ids": brief.get("references", []),
            "confidence": 0.93,
            "validation_status": "validated",
        },
        {
            "scene_id": "scene_discussion",
            "order": 5,
            "title": "AI 同学讨论",
            "scene_type": "discussion",
            "estimated_minutes": 3,
            "required": True,
            "knowledge_point_ids": ["kp_learning_rate"],
            "learning_goal_ids": ["goal_learning_rate"],
            "content": {
                "question": "学习率越大，模型训练是否一定越快？",
                "viewpoints": ["较大步长可能加快早期下降", "过大步长可能越过最低点并震荡"],
            },
            "source_ids": brief.get("references", []),
            "confidence": 0.88,
            "validation_status": "validated",
        },
        {
            "scene_id": "scene_quiz",
            "order": 6,
            "title": "即时测验",
            "scene_type": "quiz",
            "estimated_minutes": 3,
            "required": True,
            "knowledge_point_ids": kp_ids,
            "learning_goal_ids": goal_ids,
            "content": {
                "questions": default_quiz_questions(),
            },
            "source_ids": brief.get("references", []),
            "confidence": 0.9,
            "validation_status": "validated",
        },
        {
            "scene_id": "scene_code_demo",
            "order": 7,
            "title": "代码案例",
            "scene_type": "code_demo",
            "estimated_minutes": 4,
            "required": True,
            "knowledge_point_ids": ["kp_gradient", "kp_learning_rate"],
            "learning_goal_ids": goal_ids,
            "content": {
                "language": "python",
                "code": "w = 3.0\nlr = 0.1\nfor epoch in range(8):\n    grad = 2 * (w - 1)\n    w = w - lr * grad\n    print(epoch, round(w, 4))",
                "explanation": "目标是让参数 w 靠近最优值 1，每轮沿负梯度方向更新。",
            },
            "source_ids": brief.get("references", []),
            "confidence": 0.89,
            "validation_status": "validated",
        },
        {
            "scene_id": "scene_summary",
            "order": 8,
            "title": "课堂总结",
            "scene_type": "summary",
            "estimated_minutes": 2,
            "required": True,
            "knowledge_point_ids": kp_ids,
            "learning_goal_ids": goal_ids,
            "content": {
                "mastered": ["梯度下降沿负梯度方向更新参数", "学习率影响参数更新步长"],
                "review": ["学习率过大导致震荡", "收敛缓慢、震荡和发散的区别"],
                "next": ["完成学习率专项练习", "回看学习率交互模拟"],
            },
            "source_ids": brief.get("references", []),
            "confidence": 0.9,
            "validation_status": "validated",
        },
    ]
    return {
        "classroom_id": classroom_id,
        "title": brief.get("title") or "梯度下降与学习率沉浸式课堂",
        "topic": brief.get("topic") or "梯度下降与学习率",
        "source": source,
        "version": 1,
        "generated_at": now,
        "estimated_minutes": brief.get("estimated_minutes", 25),
        "scenes": scenes,
        "validation_status": "validated",
        "summary": "通过 AI 教师讲解、参数更新白板、学习率交互模拟、即时测验和代码案例理解模型训练过程。",
        "raw_brief": json.loads(json.dumps(brief, ensure_ascii=False)),
    }


def default_quiz_questions() -> list[dict[str, Any]]:
    return [
        {
            "question_id": "q_lr_too_large",
            "type": "single_choice",
            "question": "学习率过大时，训练最可能出现什么现象？",
            "options": ["稳定收敛", "损失震荡或发散", "参数不再更新", "梯度恒为 0"],
            "answer": "损失震荡或发散",
            "explanation": "步长太大会反复跨过最低点，损失难以稳定下降。",
            "knowledge_point_ids": ["kp_learning_rate", "kp_convergence"],
        },
        {
            "question_id": "q_lr_too_small",
            "type": "true_false",
            "question": "学习率越小，模型训练一定越好。",
            "options": ["正确", "错误"],
            "answer": "错误",
            "explanation": "过小学习率通常收敛很慢，训练成本升高。",
            "knowledge_point_ids": ["kp_learning_rate"],
        },
        {
            "question_id": "q_negative_gradient",
            "type": "single_choice",
            "question": "梯度下降中参数通常沿哪个方向更新？",
            "options": ["梯度方向", "负梯度方向", "随机方向", "不变"],
            "answer": "负梯度方向",
            "explanation": "负梯度方向是函数下降最快的局部方向。",
            "knowledge_point_ids": ["kp_gradient"],
        },
    ]
