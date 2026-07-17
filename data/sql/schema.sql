-- ============================================================
-- EduAgent SQLite schema
-- Keep this file aligned with backend/models/*.py.
-- ============================================================

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    nickname TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_profiles (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    knowledge_level TEXT,
    learning_goal TEXT,
    learning_history TEXT,
    cognitive_style TEXT,
    pace_preference TEXT,
    weakness TEXT,
    interest TEXT,
    chat_history TEXT,
    memory_strength TEXT,
    completeness REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE TABLE IF NOT EXISTS learning_paths (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    goal TEXT,
    stages TEXT,
    current_stage INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE TABLE IF NOT EXISTS resources (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    path_id TEXT,
    stage_id INTEGER,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    topic TEXT,
    difficulty TEXT,
    is_review BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (path_id) REFERENCES learning_paths(id)
);

CREATE TABLE IF NOT EXISTS learning_records (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    resource_id TEXT,
    action TEXT NOT NULL,
    topic TEXT,
    score REAL,
    time_spent INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

CREATE TABLE IF NOT EXISTS evaluation_reports (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    overall_score REAL NOT NULL DEFAULT 0.0,
    dimensions TEXT NOT NULL DEFAULT '[]',
    weak_topics TEXT NOT NULL DEFAULT '[]',
    suggestions TEXT NOT NULL DEFAULT '[]',
    review_plan TEXT NOT NULL DEFAULT '[]',
    source_snapshot TEXT NOT NULL DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE INDEX IF NOT EXISTS idx_student_profiles_student_id
    ON student_profiles(student_id);

CREATE INDEX IF NOT EXISTS idx_learning_paths_student_status
    ON learning_paths(student_id, status);

CREATE INDEX IF NOT EXISTS idx_resources_student_id
    ON resources(student_id);

CREATE INDEX IF NOT EXISTS idx_learning_records_student_id
    ON learning_records(student_id);

CREATE INDEX IF NOT EXISTS idx_evaluation_reports_student_id
    ON evaluation_reports(student_id);
