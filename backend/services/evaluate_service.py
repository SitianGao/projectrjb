"""Learning evaluation service —— 集成 EvaluateAgent（Day 9）

提供学习记录管理 + AI 增强多维度评估报告。
- 基础统计：overall_score、topic_scores、history、progress_stats
- AI 增强（EvaluateAgent）：dimensions、weak_topics、suggestions、review_plan
"""

from __future__ import annotations

import datetime
import json
import logging
import uuid
from collections import defaultdict
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from models.evaluation import LearningRecord

logger = logging.getLogger(__name__)


class EvaluateService:
    """学习记录管理 + 多维度评估报告（Day 9 升级：集成 EvaluateAgent）"""

    def __init__(self, profile_service, evaluate_agent=None):
        self.profile_service = profile_service
        self.evaluate_agent = evaluate_agent

    # ── 学习记录 ──────────────────────────────────────────

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

    # ── 评估入口 ──────────────────────────────────────────

    def start_evaluation(self, db: Session, student_id: str) -> Dict:
        """同步评估入口（兼容旧接口）"""
        self.profile_service.get_or_create_student(db, student_id)
        return self.build_report(db, student_id)

    async def start_evaluation_async(self, db: Session, student_id: str) -> Dict:
        """异步评估入口（供 SSE 端点使用，含 AI 增强）"""
        self.profile_service.get_or_create_student(db, student_id)
        return await self.build_report_async(db, student_id)

    # ── 核心：构建评估报告 ────────────────────────────────

    def build_report(self, db: Session, student_id: str) -> Dict:
        """构建评估报告（同步版：基础统计 + 规则化 AI 评估）

        始终包含 5 个 Day 9 字段：
        overall_score / dimensions / weak_topics / suggestions / review_plan
        """
        records = self._query_records(db, student_id)
        profile = self._get_profile(db, student_id)
        report = self._build_base_report(student_id, records)

        # AI 增强：通过 EvaluateAgent 获取 dimensions/weak_topics/suggestions/review_plan
        ai_fields = self._run_agent_eval_sync(student_id, profile, records)
        report.update(ai_fields)

        return report

    async def build_report_async(self, db: Session, student_id: str) -> Dict:
        """构建评估报告（异步版：基础统计 + LLM/AI 增强评估）"""
        records = self._query_records(db, student_id)
        profile = self._get_profile(db, student_id)
        report = self._build_base_report(student_id, records)

        # AI 增强：异步调用 EvaluateAgent
        ai_fields = await self._run_agent_eval_async(student_id, profile, records)
        report.update(ai_fields)

        return report

    # ── 基础统计（不依赖 Agent）───────────────────────────

    def _build_base_report(self, student_id: str, records: List[LearningRecord]) -> Dict:
        """纯统计报告：overall_score / topic_scores / history / progress_stats"""
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

    # ── Agent 调用（同步 / 异步）───────────────────────────

    def _run_agent_eval_sync(
        self,
        student_id: str,
        profile: Dict,
        records: List[LearningRecord],
    ) -> Dict:
        """同步调用 EvaluateAgent（规则化兜底），返回 AI 增强字段"""
        record_dicts = [self._record_to_dict(r) for r in records]
        try:
            raw = self.evaluate_agent.evaluate_sync(
                student_id=student_id,
                profile=profile,
                records=record_dicts,
                path=None,
            )
            return self._merge_agent_result(raw)
        except Exception as exc:
            logger.warning("EvaluateAgent 同步评估失败，使用内联规则兜底: %s", exc)
            return self._fallback_ai_fields(student_id, profile, record_dicts)

    async def _run_agent_eval_async(
        self,
        student_id: str,
        profile: Dict,
        records: List[LearningRecord],
    ) -> Dict:
        """异步调用 EvaluateAgent（LLM 优先），返回 AI 增强字段"""
        record_dicts = [self._record_to_dict(r) for r in records]
        try:
            raw = await self.evaluate_agent.evaluate(
                student_id=student_id,
                profile=profile,
                records=record_dicts,
                path=None,
            )
            return self._merge_agent_result(raw)
        except Exception as exc:
            logger.warning("EvaluateAgent 异步评估失败，使用规则兜底: %s", exc)
            return self._fallback_ai_fields(student_id, profile, record_dicts)

    def _fallback_ai_fields(
        self,
        student_id: str,
        profile: Dict,
        records: List[Dict],
    ) -> Dict:
        """当 Agent 完全不可用时，由 service 层直接生成 AI 字段"""
        # 直接调用 agent 的静态规则方法（不依赖 LLM）
        if self.evaluate_agent:
            raw = self.evaluate_agent._rule_based_evaluate(
                student_id=student_id,
                profile=profile,
                records=records,
                path=None,
            )
            return self._merge_agent_result(raw)
        return {
            "dimensions": [],
            "weak_topics": [],
            "suggestions": ["暂无评估建议，请先完成一些学习任务"],
            "review_plan": [],
        }

    @staticmethod
    def _merge_agent_result(raw: str) -> Dict:
        """解析 Agent 输出 JSON，提取 4 个 AI 增强字段"""
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            logger.warning("Agent 返回非 JSON，使用空 AI 字段")
            return {
                "dimensions": [],
                "weak_topics": [],
                "suggestions": [],
                "review_plan": [],
            }
        return {
            "dimensions": data.get("dimensions", []),
            "weak_topics": data.get("weak_topics", []),
            "suggestions": data.get("suggestions", []),
            "review_plan": data.get("review_plan", []),
        }

    # ── 辅助 ──────────────────────────────────────────────

    def get_progress_stats(self, db: Session, student_id: str) -> Dict:
        return self.build_report(db, student_id).get("progress_stats", {})

    @staticmethod
    def _query_records(db: Session, student_id: str) -> List[LearningRecord]:
        return (
            db.query(LearningRecord)
            .filter(LearningRecord.student_id == student_id)
            .order_by(LearningRecord.created_at.asc())
            .all()
        )

    def _get_profile(self, db: Session, student_id: str) -> Dict:
        """获取学生画像 dict（供 Agent 使用）"""
        try:
            profile = self.profile_service.get_profile(db, student_id)
            return profile if isinstance(profile, dict) else {}
        except Exception:
            return {}

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
