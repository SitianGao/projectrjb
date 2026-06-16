"""Learning evaluation service."""

from __future__ import annotations

import datetime
import uuid
from collections import defaultdict
from typing import Dict, Optional

from sqlalchemy.orm import Session

from models.evaluation import LearningRecord


class EvaluateService:
    """Stores learning records and computes a lightweight evaluation report."""

    def __init__(self, profile_service):
        self.profile_service = profile_service

    def start_evaluation(self, db: Session, student_id: str) -> Dict:
        self.profile_service.get_or_create_student(db, student_id)
        return self.build_report(db, student_id)

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
        self.profile_service.get_or_create_student(db, student_id)
        records = (
            db.query(LearningRecord)
            .filter(LearningRecord.student_id == student_id)
            .order_by(LearningRecord.created_at.asc())
            .all()
        )

        scored = [r for r in records if r.score is not None]
        completed = [r for r in records if r.action in {"complete", "answer"}]
        total_time = sum(r.time_spent or 0 for r in records)

        if scored:
            overall = round(sum(float(r.score) for r in scored) / len(scored))
        elif records:
            overall = 60
        else:
            overall = 0

        by_topic = defaultdict(list)
        for record in scored:
            by_topic[record.topic or "综合"].append(float(record.score))

        topic_scores = []
        for topic, scores in by_topic.items():
            score = round(sum(scores) / len(scores))
            topic_scores.append({
                "topic": topic,
                "score": score,
                "level": _score_level(score),
            })

        history_by_day = defaultdict(lambda: {"score_sum": 0.0, "score_count": 0, "tasks": 0})
        for record in records:
            day = (record.created_at or datetime.datetime.utcnow()).date().isoformat()
            history_by_day[day]["tasks"] += 1
            if record.score is not None:
                history_by_day[day]["score_sum"] += float(record.score)
                history_by_day[day]["score_count"] += 1

        history = []
        for day, item in sorted(history_by_day.items()):
            score = round(item["score_sum"] / item["score_count"]) if item["score_count"] else overall
            history.append({"date": day, "score": score, "tasks": item["tasks"]})

        recent_trend = "flat"
        if len(history) >= 2:
            recent_trend = "up" if history[-1]["score"] >= history[-2]["score"] else "down"

        total_topics = max(len(topic_scores), 1 if records else 0)
        mastered = sum(1 for item in topic_scores if item["score"] >= 80)
        learning = sum(1 for item in topic_scores if 60 <= item["score"] < 80)
        not_started = max(total_topics - mastered - learning, 0)

        return {
            "student_id": student_id,
            "overall_score": overall,
            "overallScore": overall,
            "recent_trend": recent_trend,
            "recentTrend": recent_trend,
            "completed_tasks": len(completed),
            "completedTasks": len(completed),
            "total_time": total_time,
            "totalTime": total_time,
            "topic_scores": topic_scores,
            "topicScores": topic_scores,
            "history": history,
            "progress_stats": {
                "total_topics": total_topics,
                "mastered_topics": mastered,
                "learning_topics": learning,
                "not_started_topics": not_started,
                "totalTopics": total_topics,
                "masteredTopics": mastered,
                "learningTopics": learning,
                "notStartedTopics": not_started,
            },
            "records": [self._record_to_dict(record) for record in records[-20:]],
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }

    def get_progress_stats(self, db: Session, student_id: str) -> Dict:
        return self.build_report(db, student_id)["progress_stats"]

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


def _score_level(score: int) -> str:
    if score >= 85:
        return "优秀"
    if score >= 70:
        return "良好"
    if score >= 60:
        return "需提升"
    return "薄弱"
