"""Database connection helpers for the backend."""

import logging
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL, SEED_DEMO_DATA
from models import Base


logger = logging.getLogger(__name__)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Yield one database session for a FastAPI request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all SQLAlchemy tables registered on Base and seed demo data."""
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_compat_columns()
    seed_demo_data()


def _ensure_sqlite_compat_columns():
    """为已有比赛演示库补充 create_all 无法新增的列。"""
    if not DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        user_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()
        }
        if user_columns and "is_demo" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_demo BOOLEAN DEFAULT 0 NOT NULL"))
            logger.info("数据库迁移完成：users.is_demo")
        if user_columns:
            conn.execute(text("""
                UPDATE users
                SET is_demo = 1
                WHERE id = 'demo_student' OR username = 'demo_student'
            """))

        path_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(learning_paths)")).fetchall()
        }
        path_migrations = {
            "user_id": "VARCHAR(36)",
            "course_id": "VARCHAR(36)",
            "current_stage_id": "VARCHAR(64)",
            "estimated_days": "INTEGER",
            "generation_source": "VARCHAR(30) DEFAULT 'legacy'",
            "generated_by": "VARCHAR(80)",
            "provider": "VARCHAR(50)",
            "model": "VARCHAR(100)",
            "agent_run_id": "VARCHAR(64)",
            "profile_version": "INTEGER",
            "fallback_used": "BOOLEAN DEFAULT 0",
            "fallback_type": "VARCHAR(50)",
            "generated_at": "DATETIME",
        }
        for column, ddl in path_migrations.items():
            if column not in path_columns:
                conn.execute(text(f"ALTER TABLE learning_paths ADD COLUMN {column} {ddl}"))
                logger.info("数据库迁移完成：learning_paths.%s", column)

        conn.execute(text("""
            UPDATE learning_paths
            SET course_id = (
                SELECT courses.id
                FROM courses
                WHERE courses.student_id = learning_paths.student_id
                LIMIT 1
            )
            WHERE course_id IS NULL
        """))
        conn.execute(text("""
            UPDATE learning_paths
            SET user_id = (
                SELECT courses.user_id
                FROM courses
                WHERE courses.id = learning_paths.course_id
                LIMIT 1
            )
            WHERE user_id IS NULL
        """))
        conn.execute(text("""
            UPDATE learning_paths
            SET generation_source = 'legacy'
            WHERE generation_source IS NULL OR generation_source = ''
        """))

        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(resources)")).fetchall()
        }
        resource_migrations = {
            "source_refs": "TEXT DEFAULT '[]'",
            "artifact_url": "VARCHAR(500)",
            "mime_type": "VARCHAR(100)",
            "course_id": "VARCHAR(36)",
            "stage_id": "VARCHAR(64)",
            "task_id": "VARCHAR(100)",
            "parent_resource_id": "VARCHAR(36)",
            "trigger_source": "VARCHAR(40) DEFAULT 'manual'",
            "trigger_context": "TEXT DEFAULT '{}'",
            "variant_type": "VARCHAR(50)",
            "generation_version": "VARCHAR(30) DEFAULT '1'",
            "generation_status": "VARCHAR(20) DEFAULT 'ready'",
            "generation_source": "VARCHAR(30) DEFAULT 'agent'",
            "fallback_type": "VARCHAR(50)",
            "idempotency_key": "VARCHAR(64)",
        }
        for column, ddl in resource_migrations.items():
            if column not in columns:
                conn.execute(text(f"ALTER TABLE resources ADD COLUMN {column} {ddl}"))
                logger.info("数据库迁移完成：resources.%s", column)

        conn.execute(text("""
            UPDATE resources
            SET course_id = (
                SELECT courses.id
                FROM courses
                WHERE courses.student_id = resources.student_id
                LIMIT 1
            )
            WHERE course_id IS NULL
        """))
        conn.execute(text("""
            UPDATE resources
            SET generation_version = '1'
            WHERE generation_version IS NULL OR generation_version = ''
        """))
        conn.execute(text("""
            UPDATE resources
            SET generation_status = 'ready'
            WHERE generation_status IS NULL OR generation_status = ''
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_resources_context_lookup "
            "ON resources (student_id, task_id, type, difficulty, generation_version)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_resources_idempotency_key "
            "ON resources (idempotency_key)"
        ))

        wrong_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(wrong_questions)")).fetchall()
        }
        if wrong_columns:
            wrong_migrations = {
                "resource_id": "VARCHAR(36)",
                "question": "TEXT DEFAULT ''",
                "question_text": "TEXT",
                "options": "TEXT DEFAULT '[]'",
                "user_answer": "TEXT",
                "correct_answer": "TEXT",
                "explanation": "TEXT",
                "difficulty": "VARCHAR(20)",
                "tags": "TEXT DEFAULT '[]'",
                "wrong_count": "INTEGER DEFAULT 1",
                "correct_streak": "INTEGER DEFAULT 0",
                "status": "VARCHAR(20) DEFAULT 'unmastered'",
                "last_wrong_at": "DATETIME",
                "next_review_at": "DATETIME",
                "created_at": "DATETIME",
            }
            for column, ddl in wrong_migrations.items():
                if column not in wrong_columns:
                    conn.execute(text(f"ALTER TABLE wrong_questions ADD COLUMN {column} {ddl}"))
                    logger.info("数据库迁移完成：wrong_questions.%s", column)

        # ── 第1轮改造：EvaluationReport 新增字段 ──
        eval_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(evaluation_reports)")).fetchall()
        }
        eval_migrations = {
            "has_sufficient_data": "BOOLEAN DEFAULT 0 NOT NULL",
            "insufficient_reason": "TEXT DEFAULT ''",
            "generation_source": "VARCHAR(30) DEFAULT 'rule'",
            "provider": "VARCHAR(50)",
            "model": "VARCHAR(100)",
            "fallback_used": "BOOLEAN DEFAULT 0 NOT NULL",
            "fallback_reason": "TEXT",
        }
        for column, ddl in eval_migrations.items():
            if column not in eval_columns:
                conn.execute(text(f"ALTER TABLE evaluation_reports ADD COLUMN {column} {ddl}"))
                logger.info("数据库迁移完成：evaluation_reports.%s", column)

        # ── 第2轮改造：EvaluationReport 新增字段 ──
        eval_v2_migrations = {
            "course_id": "VARCHAR(36)",
            "evidence_hash": "VARCHAR(64)",
            "evidence_count": "INTEGER DEFAULT 0",
            "evidence_summary": "TEXT DEFAULT '{}'",
            "trigger": "VARCHAR(20) DEFAULT 'auto'",
            "scope_type": "VARCHAR(30) DEFAULT 'last_30_days'",
            "scope_start_at": "DATETIME",
            "scope_end_at": "DATETIME",
            "supersedes_report_id": "VARCHAR(36)",
            "statistics_json": "TEXT DEFAULT '{}'",
            "agent_result_json": "TEXT DEFAULT '{}'",
        }
        for column, ddl in eval_v2_migrations.items():
            if column not in eval_columns:
                conn.execute(text(f"ALTER TABLE evaluation_reports ADD COLUMN {column} {ddl}"))
                logger.info("数据库迁移完成：evaluation_reports.%s", column)

        # 删除旧评估报告（第1+2轮改造）
        if eval_columns:
            deleted = conn.execute(text(
                "DELETE FROM evaluation_reports WHERE has_sufficient_data = 0 AND evidence_hash IS NULL"
            )).rowcount
            if deleted:
                logger.info("数据库清理完成：删除 %d 份旧评估报告", deleted)

        # ── 第3轮改造：新增表 ──
        for table_name, ddl in [
            ("path_adjustment_logs", """
                CREATE TABLE IF NOT EXISTS path_adjustment_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    course_id TEXT,
                    learning_path_id TEXT,
                    source_evaluation_id TEXT,
                    adjustment_key TEXT,
                    action TEXT NOT NULL,
                    knowledge_point TEXT,
                    target_stage_id TEXT,
                    target_task_id TEXT,
                    suggested_resource_type TEXT,
                    before_state TEXT DEFAULT '{}',
                    after_state TEXT DEFAULT '{}',
                    reason TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'suggested',
                    applied_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """),
            ("profile_update_logs", """
                CREATE TABLE IF NOT EXISTS profile_update_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    course_id TEXT,
                    student_id TEXT NOT NULL,
                    source_evaluation_id TEXT,
                    field TEXT NOT NULL,
                    before_value TEXT,
                    after_value TEXT,
                    reason TEXT,
                    confidence REAL DEFAULT 0.0,
                    evidence_refs TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'suggested',
                    applied_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """),
        ]:
            existing = conn.execute(text(
                f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )).scalar()
            if not existing:
                conn.execute(text(ddl))
                logger.info("数据库迁移完成：创建表 %s", table_name)


def seed_demo_data():
    """Import the fixed demo student into an empty SQLite database."""
    if not SEED_DEMO_DATA:
        logger.info("跳过演示数据导入：SEED_DEMO_DATA=false")
        return

    if not DATABASE_URL.startswith("sqlite"):
        logger.info("跳过演示数据导入：当前数据库不是 SQLite")
        return

    seed_path = Path(__file__).resolve().parents[1] / "data" / "sql" / "seed.sql"
    if not seed_path.exists():
        logger.warning("演示数据文件不存在：%s", seed_path)
        return

    with engine.begin() as conn:
        demo_count = conn.execute(
            text("SELECT COUNT(*) FROM students WHERE id = :student_id"),
            {"student_id": "demo-student-01"},
        ).scalar() or 0
        if demo_count > 0:
            logger.info("数据库已有固定演示学生，跳过演示数据导入")
            return

        dbapi_conn = getattr(conn.connection, "driver_connection", None)
        if dbapi_conn is None:
            dbapi_conn = conn.connection.connection

        dbapi_conn.executescript(seed_path.read_text(encoding="utf-8"))
        logger.info("演示数据导入完成：%s", seed_path)
