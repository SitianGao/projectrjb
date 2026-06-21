param(
    [string]$DatabasePath = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($DatabasePath)) {
    $DatabasePath = Join-Path $ProjectRoot "eduagent.db"
}

$SchemaPath = Join-Path $ProjectRoot "data\sql\schema.sql"
$SeedPath = Join-Path $ProjectRoot "data\sql\seed.sql"
$ResolvedDatabasePath = [System.IO.Path]::GetFullPath($DatabasePath)

if (-not (Test-Path $SchemaPath)) {
    throw "Schema file not found: $SchemaPath"
}

if (-not (Test-Path $SeedPath)) {
    throw "Seed file not found: $SeedPath"
}

$pythonCode = @"
import pathlib
import sqlite3

db_path = pathlib.Path(r'''$ResolvedDatabasePath''')
schema_path = pathlib.Path(r'''$SchemaPath''')
seed_path = pathlib.Path(r'''$SeedPath''')

db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
try:
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.executescript(seed_path.read_text(encoding="utf-8"))
    conn.commit()

    tables = [
        "students",
        "student_profiles",
        "learning_paths",
        "resources",
        "learning_records",
        "evaluation_reports",
    ]
    print(f"Database initialized: {db_path}")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")
finally:
    conn.close()
"@

$pythonCode | python -
