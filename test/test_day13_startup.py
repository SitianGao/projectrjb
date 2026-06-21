"""Day 13 startup and seed-data checks."""

from __future__ import annotations

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_day13_schema_and_seed_create_demo_student():
    schema_sql = (PROJECT_ROOT / "data" / "sql" / "schema.sql").read_text(encoding="utf-8")
    seed_sql = (PROJECT_ROOT / "data" / "sql" / "seed.sql").read_text(encoding="utf-8")

    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(schema_sql)
        conn.executescript(seed_sql)
        conn.commit()

        student = conn.execute(
            "SELECT id, nickname FROM students WHERE id = ?",
            ("demo-student-01",),
        ).fetchone()
        profile_count = conn.execute(
            "SELECT COUNT(*) FROM student_profiles WHERE student_id = ?",
            ("demo-student-01",),
        ).fetchone()[0]
        path_count = conn.execute(
            "SELECT COUNT(*) FROM learning_paths WHERE student_id = ? AND status = 'active'",
            ("demo-student-01",),
        ).fetchone()[0]
        resource_count = conn.execute(
            "SELECT COUNT(*) FROM resources WHERE student_id = ?",
            ("demo-student-01",),
        ).fetchone()[0]

        assert student == ("demo-student-01", "演示学生")
        assert profile_count >= 1
        assert path_count >= 1
        assert resource_count >= 1
    finally:
        conn.close()
