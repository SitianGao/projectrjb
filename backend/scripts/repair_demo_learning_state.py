"""Dry-run/apply repair for the demo course learning path state.

The script never deletes data. It only updates path statuses for the current
demo user/course when a completed superseded path should be the effective
course state.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, init_db
from models.auth import Course, User
from models.learning_path import LearningPath, LearningTask
from scripts.init_demo_course import COURSE_GOAL, COURSE_ID, COURSE_TITLE, DEMO_USER_ID


def _counts(db, path_id: str) -> tuple[int, int]:
    tasks = db.query(LearningTask).filter(LearningTask.path_id == path_id).all()
    total = len({task.task_id for task in tasks})
    completed = len({task.task_id for task in tasks if task.status == "completed"})
    return completed, total


def repair_demo_learning_state(*, apply: bool = False) -> dict:
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == DEMO_USER_ID).first()
        course = db.query(Course).filter(Course.id == COURSE_ID).first()
        if not user or not course:
            raise RuntimeError("demo_student 或 ai_deep_learning_demo 不存在")

        paths = (
            db.query(LearningPath)
            .filter(
                LearningPath.user_id == DEMO_USER_ID,
                LearningPath.course_id == COURSE_ID,
                LearningPath.status != "archived",
            )
            .order_by(LearningPath.version.asc())
            .all()
        )
        report_paths = []
        completed_candidates = []
        for path in paths:
            completed, total = _counts(db, path.id)
            item = {
                "path_id": path.id,
                "version": path.version,
                "status": path.status,
                "completed_tasks": completed,
                "total_tasks": total,
                "percent": round(completed / total * 100) if total else 0,
            }
            report_paths.append(item)
            if total > 0 and completed >= total:
                completed_candidates.append(path)

        target = completed_candidates[-1] if completed_candidates else None
        planned_updates = []
        if target:
            for path in paths:
                next_status = "completed" if path.id == target.id else path.status
                if path.status == "active" and path.id != target.id:
                    next_status = "superseded"
                if path.status == "superseded" and path.id == target.id:
                    next_status = "completed"
                if next_status != path.status:
                    planned_updates.append({
                        "path_id": path.id,
                        "from": path.status,
                        "to": next_status,
                    })
                    if apply:
                        path.status = next_status

        if apply:
            course.title = COURSE_TITLE
            course.goal = COURSE_GOAL
            course.user_id = DEMO_USER_ID
            user.active_course_id = COURSE_ID
            db.commit()

        return {
            "mode": "apply" if apply else "dry-run",
            "user_id": DEMO_USER_ID,
            "course_id": COURSE_ID,
            "paths": report_paths,
            "target_path_id": target.id if target else None,
            "planned_updates": planned_updates,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="apply status updates")
    args = parser.parse_args()
    result = repair_demo_learning_state(apply=args.apply)
    for key, value in result.items():
        print(f"{key}: {value}")
