"""把 demo_student 的学习进度恢复到可重复录制的 Seed 状态。"""

from __future__ import annotations

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, init_db
from models.auth import Course
from models.learning_path import AgentRun, LearningPath, LearningStage, LearningTask
from models.study_session import StudySession
from scripts.init_demo_course import (
    COURSE_ID,
    DEMO_STAGES,
    DEMO_STUDENT_ID,
    DEMO_USER_ID,
    init_demo_course,
)


def reset_demo_student() -> dict:
    init_db()
    init_demo_course()
    db = SessionLocal()
    try:
        paths = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == DEMO_STUDENT_ID,
                LearningPath.course_id == COURSE_ID,
            )
            .order_by(LearningPath.version.desc())
            .all()
        )
        path = paths[0] if paths else None
        if not path:
            raise RuntimeError("demo_student 学习路径不存在")
        for old_path in paths[1:]:
            old_path.status = "superseded"

        course = db.query(Course).filter(Course.id == COURSE_ID).first()
        if course:
            from scripts.init_demo_course import COURSE_TITLE

            course.title = COURSE_TITLE

        db.query(LearningTask).filter(LearningTask.path_id == path.id).delete(
            synchronize_session=False
        )
        db.query(LearningStage).filter(LearningStage.path_id == path.id).delete(
            synchronize_session=False
        )
        db.query(AgentRun).filter(
            AgentRun.user_id == DEMO_USER_ID,
            AgentRun.course_id == COURSE_ID,
        ).delete(synchronize_session=False)
        db.query(StudySession).filter(
            StudySession.user_id == DEMO_USER_ID,
            StudySession.course_id == COURSE_ID,
        ).delete(synchronize_session=False)
        path.stages = json.dumps(DEMO_STAGES, ensure_ascii=False)
        path.current_stage = 2
        path.current_stage_id = "stage_gradient_descent"
        path.status = "active"
        path.generation_source = "seed"
        path.generated_by = "backend/scripts/init_demo_course.py"
        path.provider = None
        path.model = None
        path.agent_run_id = None
        path.fallback_used = False
        path.fallback_type = None
        path.generated_at = datetime.datetime.utcnow()
        db.commit()

        from deps import planner_service

        planner_service.ensure_normalized_entities(db, path)
        return {"user_id": DEMO_USER_ID, "course_id": COURSE_ID, "path_id": path.id}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    result = reset_demo_student()
    print(
        "demo_student 已重置："
        f"course={result['course_id']} path={result['path_id']}"
    )
