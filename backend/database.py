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
    seed_demo_data()


<<<<<<< Updated upstream
=======
def _ensure_sqlite_compat_columns():
    """为已有比赛演示库补充 create_all 无法新增的列。"""
    if not DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(resources)")).fetchall()
        }
        if "source_refs" not in columns:
            conn.execute(text("ALTER TABLE resources ADD COLUMN source_refs TEXT DEFAULT '[]'"))
            logger.info("数据库迁移完成：resources.source_refs")
        if "artifact_url" not in columns:
            conn.execute(text("ALTER TABLE resources ADD COLUMN artifact_url VARCHAR(500)"))
            logger.info("数据库迁移完成：resources.artifact_url")
        if "mime_type" not in columns:
            conn.execute(text("ALTER TABLE resources ADD COLUMN mime_type VARCHAR(100)"))
            logger.info("数据库迁移完成：resources.mime_type")
        if "stage_id" not in columns:
            conn.execute(text("ALTER TABLE resources ADD COLUMN stage_id INTEGER"))
            logger.info("数据库迁移完成：resources.stage_id")


>>>>>>> Stashed changes
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
