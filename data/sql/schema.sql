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
    course_id TEXT,
    path_id TEXT,
    stage_id TEXT,
    task_id TEXT,
    parent_resource_id TEXT,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    topic TEXT,
    difficulty TEXT,
    is_review BOOLEAN DEFAULT 0,
    source_refs TEXT DEFAULT '[]',
    artifact_url TEXT,
    mime_type TEXT,
    trigger_source TEXT DEFAULT 'manual',
    trigger_context TEXT DEFAULT '{}',
    variant_type TEXT,
    generation_version TEXT DEFAULT '1',
    generation_status TEXT DEFAULT 'ready',
    generation_source TEXT DEFAULT 'agent',
    fallback_type TEXT,
    idempotency_key TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (path_id) REFERENCES learning_paths(id),
    FOREIGN KEY (parent_resource_id) REFERENCES resources(id)
);

CREATE INDEX IF NOT EXISTS ix_resources_context_lookup
ON resources(student_id, task_id, type, difficulty, generation_version);

CREATE TABLE IF NOT EXISTS resource_user_states (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    is_favorite BOOLEAN DEFAULT 0 NOT NULL,
    learning_status TEXT DEFAULT 'not_started' NOT NULL,
    opened_count INTEGER DEFAULT 0 NOT NULL,
    last_opened_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, resource_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
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
    course_id TEXT,
    overall_score REAL,                      -- NULL when insufficient data
    dimensions TEXT NOT NULL DEFAULT '[]',
    weak_topics TEXT NOT NULL DEFAULT '[]',
    suggestions TEXT NOT NULL DEFAULT '[]',
    review_plan TEXT NOT NULL DEFAULT '[]',
    source_snapshot TEXT NOT NULL DEFAULT '{}',
    -- v1: data sufficiency
    has_sufficient_data BOOLEAN DEFAULT 0 NOT NULL,
    insufficient_reason TEXT DEFAULT '',
    -- v1: provenance
    generation_source TEXT DEFAULT 'rule',
    provider TEXT,
    model TEXT,
    fallback_used BOOLEAN DEFAULT 0 NOT NULL,
    fallback_reason TEXT,
    -- v2: evidence & versioning
    evidence_hash TEXT,
    evidence_count INTEGER DEFAULT 0,
    evidence_summary TEXT DEFAULT '{}',
    trigger TEXT DEFAULT 'auto',
    scope_type TEXT DEFAULT 'last_30_days',
    scope_start_at DATETIME,
    scope_end_at DATETIME,
    supersedes_report_id TEXT,
    statistics_json TEXT DEFAULT '{}',
    agent_result_json TEXT DEFAULT '{}',
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
