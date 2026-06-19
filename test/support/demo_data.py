"""Deterministic demo data for Day 11 captain-owned E2E tests."""

from __future__ import annotations

import json

from models.evaluation import LearningRecord
from models.learning_path import LearningPath
from models.resource import Resource
from models.student import Student, StudentProfile


DAY11_STUDENT_ID = "demo-student-01"


def ensure_demo_student(db, student_id: str = DAY11_STUDENT_ID) -> dict:
    """Create the fixed Day 11 demo student and related records if missing."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        student = Student(id=student_id, nickname="演示学生")
        db.add(student)
        db.flush()

    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.student_id == student_id)
        .order_by(StudentProfile.version.desc())
        .first()
    )
    if not profile:
        profile = StudentProfile(
            id="profile_day11_demo_001",
            student_id=student_id,
            version=1,
            knowledge_level="中级，具备 Python 基础，正在系统学习机器学习",
            learning_goal="掌握机器学习基础并补齐梯度下降薄弱点",
            learning_history=json.dumps(["完成 Python 基础", "阅读机器学习入门材料"], ensure_ascii=False),
            cognitive_style="动手型学习者",
            pace_preference="中速均衡型",
            weakness=json.dumps(["梯度下降", "神经网络基础"], ensure_ascii=False),
            interest=json.dumps(["机器学习", "深度学习"], ensure_ascii=False),
            memory_strength=json.dumps({"线性回归": 8.5, "梯度下降": 4.5}, ensure_ascii=False),
            completeness=0.86,
        )
        db.add(profile)
        db.flush()

    path = (
        db.query(LearningPath)
        .filter(LearningPath.student_id == student_id, LearningPath.status == "active")
        .order_by(LearningPath.version.desc())
        .first()
    )
    if not path:
        path = db.query(LearningPath).filter(LearningPath.id == "path_day11_demo_001").first()
        if not path:
            path = LearningPath(
                id="path_day11_demo_001",
                student_id=student_id,
                version=1,
                goal="完成机器学习基础、梯度下降和神经网络入门",
                stages=json.dumps(_demo_stages(), ensure_ascii=False),
                current_stage=1,
                status="active",
            )
            db.add(path)
        else:
            path.status = "active"
        db.flush()

    resource = db.query(Resource).filter(Resource.id == "res_day11_demo_001").first()
    if not resource:
        resource = Resource(
            id="res_day11_demo_001",
            student_id=student_id,
            path_id=path.id,
            type="document",
            title="Day11 机器学习基础讲义",
            content="## 机器学习基础\n\n监督学习包含数据准备、模型训练、验证评估和迭代优化。",
            topic="机器学习基础",
            difficulty="中级",
            is_review=False,
        )
        db.add(resource)
        db.flush()

    record = db.query(LearningRecord).filter(LearningRecord.id == "rec_day11_demo_001").first()
    if not record:
        record = LearningRecord(
            id="rec_day11_demo_001",
            student_id=student_id,
            resource_id=resource.id,
            action="complete",
            topic="机器学习基础",
            score=0.88,
            time_spent=2400,
        )
        db.add(record)

    db.commit()
    return {
        "student_id": student_id,
        "path_id": path.id,
        "resource_id": resource.id,
    }


def _demo_stages() -> list[dict]:
    return [
        {
            "stage_id": 1,
            "title": "机器学习基础巩固",
            "description": "复习监督学习、线性回归和模型评估。",
            "objectives": ["理解监督学习流程", "掌握训练/测试划分"],
            "topics": ["机器学习基础", "线性回归"],
            "estimated_days": 3,
            "difficulty": "中级",
            "tasks": [
                {
                    "task_id": "day11-1-1",
                    "type": "study",
                    "description": "阅读机器学习基础讲义",
                    "estimated_days": 1,
                    "difficulty": "中级",
                    "status": "completed",
                }
            ],
        },
        {
            "stage_id": 2,
            "title": "梯度下降专项",
            "description": "补齐梯度下降和学习率理解。",
            "objectives": ["解释学习率影响", "手算一轮参数更新"],
            "topics": ["梯度下降", "学习率"],
            "estimated_days": 4,
            "difficulty": "中级",
            "tasks": [],
        },
    ]
