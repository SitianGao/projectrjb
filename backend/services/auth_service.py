"""数据库账号认证与课程隔离服务。"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import os
import secrets
import uuid

from sqlalchemy.orm import Session

from api.response import ApiError
from models.auth import AuthToken, Course, User
from models.student import Student


PBKDF2_ITERATIONS = 240_000
TOKEN_LIFETIME_DAYS = 7


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        _, iterations, salt_hex, expected = encoded.split("$", 3)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        ).hex()
        return hmac.compare_digest(digest, expected)
    except (TypeError, ValueError):
        return False


class AuthService:
    def register(self, db: Session, username: str, password: str, phone: str = "") -> dict:
        username = username.strip()
        if len(username) < 3 or len(password) < 6:
            raise ApiError("VALIDATION_ERROR", "用户名至少 3 位，密码至少 6 位")
        if db.query(User).filter(User.username == username).first():
            raise ApiError("USERNAME_EXISTS", "用户名已存在")

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=_hash_password(password),
            name=username,
            phone=phone,
            bio="",
        )
        db.add(user)
        db.flush()
        course = self._create_course(db, user, "我的第一门课程", "")
        user.active_course_id = course.id
        db.commit()
        return self._issue_session(db, user)

    def login(self, db: Session, username: str, password: str) -> dict:
        user = db.query(User).filter(User.username == username.strip()).first()
        if not user or not _verify_password(password, user.password_hash):
            raise ApiError("INVALID_CREDENTIALS", "用户名或密码错误")
        return self._issue_session(db, user)

    def logout(self, db: Session, token: str) -> None:
        db.query(AuthToken).filter(AuthToken.token_hash == self._token_hash(token)).delete()
        db.commit()

    def authenticate(self, db: Session, token: str) -> User:
        token_row = db.query(AuthToken).filter(
            AuthToken.token_hash == self._token_hash(token),
            AuthToken.expires_at > datetime.datetime.utcnow(),
        ).first()
        if not token_row:
            raise ApiError("UNAUTHORIZED", "登录已过期，请重新登录", status_code=401)
        user = db.query(User).filter(User.id == token_row.user_id).first()
        if not user:
            raise ApiError("UNAUTHORIZED", "用户不存在", status_code=401)
        return user

    def serialize_user(self, db: Session, user: User) -> dict:
        courses = db.query(Course).filter(Course.user_id == user.id).order_by(Course.created_at).all()
        active = next((course for course in courses if course.id == user.active_course_id), None)
        if not active and courses:
            active = courses[0]
            user.active_course_id = active.id
            db.commit()
        return {
            "id": user.id,
            "username": user.username,
            "name": user.name or user.username,
            "email": user.email or "",
            "phone": user.phone or "",
            "bio": user.bio or "",
            "avatar": user.avatar,
            "is_demo": bool(user.is_demo),
            "active_course_id": active.id if active else None,
            "student_id": active.student_id if active else None,
            "active_course": self._course_dict(active) if active else None,
            "courses": [self._course_dict(course) for course in courses],
        }

    def update_profile(self, db: Session, user: User, updates: dict) -> dict:
        for key in ("name", "email", "phone", "bio", "avatar"):
            if key in updates:
                setattr(user, key, updates[key])
        db.commit()
        db.refresh(user)
        return self.serialize_user(db, user)

    def change_password(self, db: Session, user: User, old_password: str, new_password: str) -> None:
        if not _verify_password(old_password, user.password_hash):
            raise ApiError("INVALID_PASSWORD", "原密码不正确")
        if len(new_password) < 6:
            raise ApiError("VALIDATION_ERROR", "新密码至少 6 位")
        user.password_hash = _hash_password(new_password)
        db.query(AuthToken).filter(AuthToken.user_id == user.id).delete()
        db.commit()

    def create_course(self, db: Session, user: User, title: str, goal: str = "") -> dict:
        if not title.strip():
            raise ApiError("VALIDATION_ERROR", "课程名称不能为空")
        course = self._create_course(db, user, title.strip(), goal.strip())
        user.active_course_id = course.id
        db.commit()
        return self.serialize_user(db, user)

    def activate_course(self, db: Session, user: User, course_id: str) -> dict:
        course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
        if not course:
            raise ApiError("COURSE_NOT_FOUND", "课程不存在或不属于当前用户", status_code=404)
        user.active_course_id = course.id
        db.commit()
        return self.serialize_user(db, user)

    def update_course(
        self,
        db: Session,
        user: User,
        course_id: str,
        title: str | None = None,
        goal: str | None = None,
    ) -> dict:
        """画像完成后用真实学习目标命名课程，不改变课程的独立 student_id。"""
        course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
        if not course:
            raise ApiError("COURSE_NOT_FOUND", "课程不存在或不属于当前用户", status_code=404)
        if title is not None:
            cleaned_title = title.strip()
            if not cleaned_title:
                raise ApiError("VALIDATION_ERROR", "课程名称不能为空")
            course.title = cleaned_title[:200]
        if goal is not None:
            course.goal = goal.strip()
        db.commit()
        return self.serialize_user(db, user)

    def get_course_dashboard(self, db: Session, user: User, course_id: str) -> dict:
        """返回课程首页聚合数据：课程信息 + 路径 + 进度 + 派生状态。"""
        from models.learning_path import LearningPath
        from models.evaluation import LearningRecord

        course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
        if not course:
            raise ApiError("COURSE_NOT_FOUND", "课程不存在或不属于当前用户", status_code=404)

        student_id = course.student_id
        path_row = (
            db.query(LearningPath)
            .filter(LearningPath.student_id == student_id, LearningPath.status == "active")
            .order_by(LearningPath.version.desc())
            .first()
        )

        path = None
        stages = []
        current_stage = None
        total_tasks = 0
        if path_row:
            import json as _json
            try:
                stages = _json.loads(path_row.stages) if isinstance(path_row.stages, str) else path_row.stages
            except (_json.JSONDecodeError, TypeError):
                stages = []
            total_tasks = sum(len(s.get("tasks", [])) for s in stages)
            current_stage_num = path_row.current_stage or 1
            for s in stages:
                if s.get("stage_id") == current_stage_num:
                    current_stage = s
                    break
            if not current_stage and stages:
                current_stage = stages[0]
            path = {
                "id": path_row.id,
                "student_id": path_row.student_id,
                "version": path_row.version,
                "goal": path_row.goal,
                "stages": stages,
                "current_stage": path_row.current_stage,
                "status": path_row.status,
            }

        # 统计已完成任务（learning_records action in ('complete','answer')）
        completed_tasks = (
            db.query(LearningRecord)
            .filter(
                LearningRecord.student_id == student_id,
                LearningRecord.action.in_(["complete", "answer"]),
            )
            .count()
        )

        # 学习时长
        total_seconds = (
            db.query(LearningRecord.time_spent)
            .filter(LearningRecord.student_id == student_id)
            .all()
        )
        learning_minutes = max(0, round(sum(r[0] or 0 for r in total_seconds) / 60))

        # 正确率
        answer_records = (
            db.query(LearningRecord)
            .filter(LearningRecord.student_id == student_id, LearningRecord.action == "answer")
            .all()
        )
        if answer_records:
            accuracy = round(
                sum(1 for r in answer_records if (r.score or 0) >= 60) / len(answer_records) * 100
            )
        else:
            accuracy = 0

        # 连续天数（基于去重日期）
        from sqlalchemy import func as _func, cast as _cast, Date as _Date
        dates = (
            db.query(_func.date(LearningRecord.created_at))
            .filter(LearningRecord.student_id == student_id)
            .distinct()
            .order_by(_func.date(LearningRecord.created_at).desc())
            .all()
        )
        streak_days = 0
        if dates:
            import datetime as _dt
            dates_list = [d[0] for d in dates]
            today = _dt.date.today()
            for i, d in enumerate(dates_list):
                if isinstance(d, _dt.datetime):
                    d = d.date()
                expected = today - _dt.timedelta(days=i)
                if d == expected:
                    streak_days = i + 1
                else:
                    break

        # ── 派生 course_status ──
        safe_total = max(total_tasks, 1)
        safe_completed = min(completed_tasks, safe_total)

        if not path:
            course_status = "path_not_generated"
        elif safe_completed == 0:
            course_status = "not_started"
        elif safe_completed >= safe_total:
            course_status = "completed"
        else:
            course_status = "in_progress"

        current_task = None
        if current_stage and course_status == "in_progress":
            stage_tasks = current_stage.get("tasks", [])
            for t in stage_tasks:
                if t.get("status") in ("active", "pending", "in_progress"):
                    current_task = {
                        "task_id": t.get("task_id", t.get("id", "")),
                        "type": t.get("type", "study"),
                        "description": t.get("description", ""),
                        "difficulty": t.get("difficulty", "初级"),
                    }
                    break
            if not current_task and stage_tasks:
                t = stage_tasks[0]
                current_task = {
                    "task_id": t.get("task_id", t.get("id", "")),
                    "type": t.get("type", "study"),
                    "description": t.get("description", ""),
                    "difficulty": t.get("difficulty", "初级"),
                }

        return {
            "course": {
                "id": course.id,
               	"student_id": course.student_id,
                "name": course.title,
                "goal": course.goal or "",
                "status": course_status,
            },
            "progress": {
                "percentage": round(safe_completed / safe_total * 100) if path else 0,
                "completed_tasks": safe_completed,
                "total_tasks": safe_total if path else 0,
                "learning_minutes": learning_minutes,
                "accuracy": accuracy,
                "streak_days": max(streak_days, 1),
            },
            "current_stage": {
                "stage_id": current_stage.get("stage_id"),
                "title": current_stage.get("title", ""),
                "description": current_stage.get("description", ""),
                "objectives": current_stage.get("objectives", []),
                "topics": current_stage.get("topics", []),
            } if current_stage else None,
            "current_task": current_task,
            "stages": stages,
        }

    def seed_demo_users(self, db: Session) -> None:
        if db.query(User).count():
            return
        for username, password, name, student_id, course_title in (
            ("student", "student123", "小明", "demo-student-01", "机器学习演示课程"),
            ("admin", "admin123", "管理员", str(uuid.uuid4()), "平台验收课程"),
        ):
            if not db.query(Student).filter(Student.id == student_id).first():
                db.add(Student(id=student_id, nickname=name))
            user = User(
                id=str(uuid.uuid4()), username=username, password_hash=_hash_password(password), name=name
            )
            db.add(user)
            db.flush()
            course = Course(
                id=str(uuid.uuid4()), user_id=user.id, student_id=student_id, title=course_title, goal=""
            )
            db.add(course)
            user.active_course_id = course.id
        db.commit()

    def _create_course(self, db: Session, user: User, title: str, goal: str) -> Course:
        student_id = str(uuid.uuid4())
        db.add(Student(id=student_id, nickname=user.name or user.username))
        course = Course(
            id=str(uuid.uuid4()), user_id=user.id, student_id=student_id, title=title, goal=goal
        )
        db.add(course)
        db.flush()
        return course

    def _issue_session(self, db: Session, user: User) -> dict:
        token = secrets.token_urlsafe(40)
        db.add(AuthToken(
            token_hash=self._token_hash(token),
            user_id=user.id,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=TOKEN_LIFETIME_DAYS),
        ))
        db.commit()
        return {"token": token, "user": self.serialize_user(db, user)}

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _course_dict(course: Course) -> dict:
        return {
            "id": course.id,
            "student_id": course.student_id,
            "title": course.title,
            "goal": course.goal or "",
            "status": course.status,
        }


auth_service = AuthService()
