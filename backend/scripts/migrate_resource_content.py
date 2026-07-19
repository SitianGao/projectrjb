"""Migrate old resource content: dry-run → convert JSON strings to clean format."""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.resource import Resource


def migrate(dry_run=True):
    db = SessionLocal()
    resources = db.query(Resource).all()
    report = {"total": len(resources), "json_string": 0, "already_object": 0,
              "markdown": 0, "unparseable": 0, "fixed": 0}

    for r in resources:
        content = r.content
        if content is None or content == "":
            continue
        if isinstance(content, str):
            trimmed = content.strip()
            if trimmed.startswith("{") or trimmed.startswith("["):
                try:
                    parsed = json.loads(trimmed)
                    report["json_string"] += 1
                    # Check if it's double-serialized (parsed is still a string)
                    if isinstance(parsed, str):
                        try:
                            parsed = json.loads(parsed)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    if not dry_run:
                        r.content = json.dumps(parsed, ensure_ascii=False)
                        report["fixed"] += 1
                        print(f"  Fixed: {r.id[:24]} type={r.type} keys={list(parsed.keys())[:5] if isinstance(parsed, dict) else f'list[{len(parsed)}]'}")
                    else:
                        print(f"  [DRY] {r.id[:24]} type={r.type} keys={list(parsed.keys())[:5] if isinstance(parsed, dict) else f'list[{len(parsed)}]'}")
                except (json.JSONDecodeError, TypeError):
                    report["unparseable"] += 1
                    print(f"  [SKIP] {r.id[:24]}: not valid JSON")
            else:
                report["markdown"] += 1
        else:
            report["already_object"] += 1

    if not dry_run and report["fixed"] > 0:
        db.commit()
        print(f"\nCommitted {report['fixed']} fixes.")
    elif dry_run:
        print(f"\nDry run — no changes made. Run with dry_run=False to apply.")

    print(f"\nReport: total={report['total']} json_string={report['json_string']} "
          f"already_object={report['already_object']} markdown={report['markdown']} "
          f"unparseable={report['unparseable']} fixed={report['fixed']}")
    db.close()


if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    print(f"Mode: {'DRY RUN' if dry else 'APPLY'}")
    migrate(dry_run=dry)
