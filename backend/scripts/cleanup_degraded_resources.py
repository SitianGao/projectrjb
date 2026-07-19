"""
清理 demo_student 的 degraded 资源。

用法：
    # 预览（默认 dry-run）
    python backend/scripts/cleanup_degraded_resources.py --student-id demo-student-ai-dl --course-id ai_deep_learning_demo --dry-run

    # 实际执行
    python backend/scripts/cleanup_degraded_resources.py --student-id demo-student-ai-dl --course-id ai_deep_learning_demo --apply

安全规则：
- 不删除 ready 资源
- 默认 dry-run，必须显式传 --apply 才修改
"""

from __future__ import annotations

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.resource import Resource


def main():
    parser = argparse.ArgumentParser(description="清理 degraded 资源")
    parser.add_argument("--student-id", required=True, help="学生 ID")
    parser.add_argument("--course-id", default=None, help="可选：限定课程 ID")
    parser.add_argument("--task-id", default=None, help="可选：限定任务 ID")
    parser.add_argument("--apply", action="store_true", help="实际执行修改（默认 dry-run）")
    parser.add_argument("--dry-run", action="store_true", default=True, help="预览模式（默认）")
    args = parser.parse_args()

    if args.apply:
        args.dry_run = False

    db = SessionLocal()
    try:
        query = db.query(Resource).filter(
            Resource.student_id == args.student_id,
            Resource.generation_status == "degraded",
        )
        if args.course_id:
            query = query.filter(Resource.course_id == args.course_id)
        if args.task_id:
            query = query.filter(Resource.task_id == args.task_id)

        degraded = query.order_by(Resource.created_at.desc()).all()

        print(f"\n{'[DRY RUN] ' if args.dry_run else ''}找到 {len(degraded)} 个 degraded 资源：\n")
        for r in degraded:
            print(f"  ID: {r.id}")
            print(f"  Course: {r.course_id} | Stage: {r.stage_id} | Task: {r.task_id}")
            print(f"  Type: {r.type} | Title: {r.title}")
            print(f"  Source: {r.generation_source} | Fallback: {r.fallback_type}")
            print(f"  Created: {r.created_at}")
            print()

        if not degraded:
            print("没有需要清理的 degraded 资源。")
            return

        ready_query = db.query(Resource).filter(
            Resource.student_id == args.student_id,
            Resource.generation_status == "ready",
        )
        if args.course_id:
            ready_query = ready_query.filter(Resource.course_id == args.course_id)
        ready_count = ready_query.count()
        print(f"同一范围内有 {ready_count} 个 ready 资源（不会被清理）。")

        if args.apply:
            confirm = input("\n确认删除以上所有 degraded 资源？(yes/no): ")
            if confirm.lower() != "yes":
                print("已取消。")
                return
            for r in degraded:
                # 标记为 failed 而非物理删除，保留审计线索
                r.generation_status = "failed"
            db.commit()
            print(f"已将 {len(degraded)} 个 degraded 资源标记为 failed。")
            print("下次访问任务时将触发 ResourceAgent v2 重新生成。")
        else:
            print("\n提示：这是 DRY RUN。若要实际执行，请添加 --apply 参数。")

    finally:
        db.close()


if __name__ == "__main__":
    main()
