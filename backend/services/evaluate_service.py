"""Learning evaluation service."""

from __future__ import annotations

import datetime
import json
import math
import uuid
from collections import defaultdict
from typing import Dict, Optional

from sqlalchemy.orm import Session

from models.evaluation import EvaluationReport, LearningRecord


class EvaluateService:
    """Stores learning records and persists Day 9 evaluation reports."""

    def __init__(self, profile_service):
        self.profile_service = profile_service

    def start_evaluation(self, db: Session, student_id: str) -> Dict:
        """Generate a fresh report from learning records and save it."""
        self.profile_service.get_or_create_student(db, student_id)
        report = self._compute_report(db, student_id)
        saved = self._save_report(db, student_id, report)
        return self._report_to_dict(saved)

    def record_learning(
        self,
        db: Session,
        student_id: str,
        action: str,
        resource_id: Optional[str] = None,
        topic: Optional[str] = None,
        score: Optional[float] = None,
        time_spent: Optional[int] = None,
    ) -> Dict:
        self.profile_service.get_or_create_student(db, student_id)
        record = LearningRecord(
            id=str(uuid.uuid4()),
            student_id=student_id,
            resource_id=resource_id,
            action=action,
            topic=topic,
            score=score,
            time_spent=time_spent,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return self._record_to_dict(record)

    def build_report(self, db: Session, student_id: str) -> Dict:
        """Return the latest saved report, creating one on first request."""
        self.profile_service.get_or_create_student(db, student_id)
        latest = (
            db.query(EvaluationReport)
            .filter(EvaluationReport.student_id == student_id)
            .order_by(EvaluationReport.created_at.desc())
            .first()
        )
        if latest:
            return self._report_to_dict(latest)
        return self.start_evaluation(db, student_id)

    def get_progress_stats(self, db: Session, student_id: str) -> Dict:
        return self.build_report(db, student_id)["progress_stats"]

    def list_records(self, db: Session, student_id: str, limit: int = 50) -> list[Dict]:
        self.profile_service.get_or_create_student(db, student_id)
        records = (
            db.query(LearningRecord)
            .filter(LearningRecord.student_id == student_id)
            .order_by(LearningRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._record_to_dict(record) for record in records]

    def _compute_report(self, db: Session, student_id: str) -> Dict:
        records = (
            db.query(LearningRecord)
            .filter(LearningRecord.student_id == student_id)
            .order_by(LearningRecord.created_at.asc())
            .all()
        )

        scored = [record for record in records if record.score is not None]
        completed = [record for record in records if record.action in {"complete", "answer"}]
        total_time = sum(record.time_spent or 0 for record in records)

        if scored:
            overall = round(sum(_score_to_percent(record.score) for record in scored) / len(scored))
        elif records:
            overall = 60
        else:
            overall = 0

        by_topic = defaultdict(list)
        for record in scored:
            by_topic[record.topic or "综合"].append(_score_to_percent(record.score))

        topic_scores = []
        for topic, scores in by_topic.items():
            score = round(sum(scores) / len(scores))
            topic_scores.append({
                "topic": topic,
                "score": score,
                "level": _score_level(score),
            })
        topic_scores.sort(key=lambda item: item["score"])

        history_by_day = defaultdict(lambda: {"score_sum": 0.0, "score_count": 0, "tasks": 0})
        for record in records:
            day = (record.created_at or datetime.datetime.utcnow()).date().isoformat()
            history_by_day[day]["tasks"] += 1
            if record.score is not None:
                history_by_day[day]["score_sum"] += _score_to_percent(record.score)
                history_by_day[day]["score_count"] += 1

        history = []
        for day, item in sorted(history_by_day.items()):
            score = round(item["score_sum"] / item["score_count"]) if item["score_count"] else overall
            history.append({"date": day, "score": score, "tasks": item["tasks"]})
        weekly_activity = _build_weekly_activity(records)
        streak_days = _compute_streak_days(records)

        recent_trend = "flat"
        if len(history) >= 2:
            recent_trend = "up" if history[-1]["score"] >= history[-2]["score"] else "down"

        total_topics = max(len(topic_scores), 1 if records else 0)
        mastered = sum(1 for item in topic_scores if item["score"] >= 80)
        learning = sum(1 for item in topic_scores if 60 <= item["score"] < 80)
        not_started = max(total_topics - mastered - learning, 0)
        weak_topics = [item["topic"] for item in topic_scores if item["score"] < 70]
        if records and not weak_topics:
            weak_topics = ["暂未检测到明显薄弱点"]

        active_days = len(history_by_day)
        avg_minutes = round(total_time / 60 / max(len(records), 1), 1) if records else 0
        progress_score = round((len(completed) / max(len(records), 1)) * 100) if records else 0
        efficiency_score = _clamp(round((overall / 100) * 70 + min(avg_minutes / 45, 1) * 30))
        review_score = _clamp(100 - len([item for item in topic_scores if item["score"] < 60]) * 20)

        dimensions = [
            {
                "name": "knowledge_mastery",
                "label": "知识掌握",
                "score": overall,
                "comment": _dimension_comment(overall, "知识掌握"),
            },
            {
                "name": "progress",
                "label": "学习进度",
                "score": progress_score,
                "comment": _dimension_comment(progress_score, "学习进度"),
            },
            {
                "name": "efficiency",
                "label": "学习效率",
                "score": efficiency_score,
                "comment": f"平均每条记录投入 {avg_minutes} 分钟，累计学习 {round(total_time / 60)} 分钟。",
            },
            {
                "name": "review_readiness",
                "label": "复习优先级",
                "score": review_score,
                "comment": "根据低分知识点和遗忘曲线安排复习。",
            },
        ]
        suggestions = _build_suggestions(overall, weak_topics, completed, records, total_time)
        review_plan = _build_review_plan(records, topic_scores)

        return {
            "student_id": student_id,
            "overall_score": overall,
            "dimensions": dimensions,
            "weak_topics": weak_topics,
            "suggestions": suggestions,
            "review_plan": review_plan,
            "recent_trend": recent_trend,
            "completed_tasks": len(completed),
            "total_time": total_time,
            "topic_scores": topic_scores,
            "history": history,
            "weekly_activity": weekly_activity,
            "weeklyActivity": weekly_activity,
            "streak_days": streak_days,
            "streakDays": streak_days,
            "progress_stats": {
                "total_topics": total_topics,
                "mastered_topics": mastered,
                "learning_topics": learning,
                "not_started_topics": not_started,
                "streak_days": streak_days,
                "weekly_activity": weekly_activity,
                "totalTopics": total_topics,
                "masteredTopics": mastered,
                "learningTopics": learning,
                "notStartedTopics": not_started,
                "streakDays": streak_days,
                "weeklyActivity": weekly_activity,
            },
            "records": [self._record_to_dict(record) for record in records[-20:]],
            "source_summary": {
                "record_count": len(records),
                "scored_count": len(scored),
                "active_days": active_days,
                "generated_by": "evaluate_service_v1",
            },
        }

    def _save_report(self, db: Session, student_id: str, report: Dict) -> EvaluationReport:
        record = EvaluationReport(
            id=str(uuid.uuid4()),
            student_id=student_id,
            overall_score=float(report["overall_score"]),
            dimensions=json.dumps(report["dimensions"], ensure_ascii=False),
            weak_topics=json.dumps(report["weak_topics"], ensure_ascii=False),
            suggestions=json.dumps(report["suggestions"], ensure_ascii=False),
            review_plan=json.dumps(report["review_plan"], ensure_ascii=False),
            source_snapshot=json.dumps({
                "topic_scores": report["topic_scores"],
                "history": report["history"],
                "weekly_activity": report["weekly_activity"],
                "streak_days": report["streak_days"],
                "progress_stats": report["progress_stats"],
                "records": report["records"],
                "source_summary": report["source_summary"],
                "recent_trend": report["recent_trend"],
                "completed_tasks": report["completed_tasks"],
                "total_time": report["total_time"],
            }, ensure_ascii=False),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def _record_to_dict(record: LearningRecord) -> Dict:
        return {
            "id": record.id,
            "student_id": record.student_id,
            "resource_id": record.resource_id,
            "action": record.action,
            "topic": record.topic,
            "score": record.score,
            "time_spent": record.time_spent,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }

    @staticmethod
    def _report_to_dict(report: EvaluationReport) -> Dict:
        snapshot = _safe_json_loads(report.source_snapshot, {})
        dimensions = _safe_json_loads(report.dimensions, [])
        weak_topics = _safe_json_loads(report.weak_topics, [])
        suggestions = _safe_json_loads(report.suggestions, [])
        review_plan = _safe_json_loads(report.review_plan, [])
        overall = round(float(report.overall_score))

        return {
            "report_id": report.id,
            "student_id": report.student_id,
            "overall_score": overall,
            "overallScore": overall,
            "dimensions": dimensions,
            "weak_topics": weak_topics,
            "weakTopics": weak_topics,
            "suggestions": suggestions,
            "review_plan": review_plan,
            "reviewPlan": review_plan,
            "recent_trend": snapshot.get("recent_trend", "flat"),
            "recentTrend": snapshot.get("recent_trend", "flat"),
            "completed_tasks": snapshot.get("completed_tasks", 0),
            "completedTasks": snapshot.get("completed_tasks", 0),
            "total_time": snapshot.get("total_time", 0),
            "totalTime": snapshot.get("total_time", 0),
            "topic_scores": snapshot.get("topic_scores", []),
            "topicScores": snapshot.get("topic_scores", []),
            "history": snapshot.get("history", []),
            "weekly_activity": snapshot.get("weekly_activity", []),
            "weeklyActivity": snapshot.get("weekly_activity", []),
            "streak_days": snapshot.get("streak_days", 0),
            "streakDays": snapshot.get("streak_days", 0),
            "progress_stats": snapshot.get("progress_stats", {}),
            "records": snapshot.get("records", []),
            "source_summary": snapshot.get("source_summary", {}),
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        }


def _score_to_percent(score: float) -> float:
    score = float(score)
    return score * 100 if 0 <= score <= 1 else score


def _score_level(score: int) -> str:
    if score >= 85:
        return "优秀"
    if score >= 70:
        return "良好"
    if score >= 60:
        return "需提升"
    return "薄弱"


def _safe_json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def _clamp(value: float, min_value: int = 0, max_value: int = 100) -> int:
    return int(max(min_value, min(max_value, value)))


def _dimension_comment(score: int, label: str) -> str:
    if score >= 85:
        return f"{label}表现优秀，可以进入更高难度任务。"
    if score >= 70:
        return f"{label}整体良好，建议继续稳定练习。"
    if score >= 60:
        return f"{label}仍有提升空间，建议针对薄弱点复盘。"
    return f"{label}偏弱，需要优先补基础并增加练习反馈。"


def _build_suggestions(
    overall: int,
    weak_topics: list[str],
    completed: list[LearningRecord],
    records: list[LearningRecord],
    total_time: int,
) -> list[str]:
    suggestions = []
    real_weak_topics = [topic for topic in weak_topics if topic != "暂未检测到明显薄弱点"]
    if overall < 70:
        suggestions.append("先回到低分知识点的基础讲解，再用 3-5 道同类练习验证掌握情况。")
    if real_weak_topics:
        suggestions.append(f"优先复习 {real_weak_topics[0]}，复习后提交一次新的练习记录。")
    if records and len(completed) / max(len(records), 1) < 0.5:
        suggestions.append("学习记录中完成类任务偏少，建议把阅读、练习、总结串成闭环。")
    if total_time < 1800 and records:
        suggestions.append("累计学习时长偏短，建议安排至少 30 分钟连续学习后再评估。")
    if not suggestions:
        suggestions.append("当前学习节奏稳定，可以增加综合题或项目式任务来巩固迁移能力。")
    return suggestions


def _build_review_plan(records: list[LearningRecord], topic_scores: list[Dict]) -> list[Dict]:
    now = datetime.datetime.utcnow()
    topic_last_seen = {}
    for record in records:
        if not record.topic:
            continue
        current = record.created_at or now
        if record.topic not in topic_last_seen or current > topic_last_seen[record.topic]:
            topic_last_seen[record.topic] = current

    score_map = {item["topic"]: item["score"] for item in topic_scores}
    topics = set(topic_last_seen) | set(score_map)
    plan = []
    for topic in topics:
        score = score_map.get(topic, 65)
        last_seen = topic_last_seen.get(topic, now)
        days_since = max((now - last_seen).total_seconds() / 86400, 0)
        strength = max(1.0, 2.0 + (score / 100) * 8.0)
        retention = math.exp(-days_since / strength)

        if score < 60 or retention < 0.45:
            urgency = "high"
            interval_days = 1
        elif score < 75 or retention < 0.65:
            urgency = "medium"
            interval_days = 3
        else:
            urgency = "low"
            interval_days = 7

        if urgency == "low" and score >= 85 and days_since < 1:
            continue

        due_date = (now + datetime.timedelta(days=interval_days)).date().isoformat()
        plan.append({
            "topic": topic,
            "urgency": urgency,
            "due_date": due_date,
            "reason": (
                f"当前掌握度约 {score} 分，距上次学习 {days_since:.1f} 天，"
                f"遗忘曲线估算记忆保持率约 {retention:.0%}。"
            ),
            "recommended_resources": ["document", "exercise"] if score < 75 else ["reading", "exercise"],
            "retention": round(retention, 3),
            "days_since_last_study": round(days_since, 1),
            "estimated_minutes": 25 if urgency == "high" else 20 if urgency == "medium" else 15,
        })

    return sorted(plan, key=lambda item: {"high": 0, "medium": 1, "low": 2}[item["urgency"]])


def _build_weekly_activity(records: list[LearningRecord]) -> list[Dict]:
    today = datetime.datetime.utcnow().date()
    start = today - datetime.timedelta(days=6)
    by_day = {
        (start + datetime.timedelta(days=offset)).isoformat(): {
            "date": (start + datetime.timedelta(days=offset)).isoformat(),
            "studied": False,
            "minutes": 0,
            "tasks": 0,
        }
        for offset in range(7)
    }

    for record in records:
        record_date = (record.created_at or datetime.datetime.utcnow()).date()
        key = record_date.isoformat()
        if key not in by_day:
            continue
        by_day[key]["studied"] = True
        by_day[key]["minutes"] += round((record.time_spent or 0) / 60)
        by_day[key]["tasks"] += 1

    return list(by_day.values())


def _compute_streak_days(records: list[LearningRecord]) -> int:
    studied_days = {
        (record.created_at or datetime.datetime.utcnow()).date()
        for record in records
    }
    if not studied_days:
        return 0

    today = datetime.datetime.utcnow().date()
    cursor = today if today in studied_days else today - datetime.timedelta(days=1)
    streak = 0
    while cursor in studied_days:
        streak += 1
        cursor -= datetime.timedelta(days=1)
    return streak
