"""
EvaluateAgent —— 学习效果评估智能体

根据学习记录、练习结果和行为数据，评估学习效果并给出优化建议，
驱动学习路径的动态调整（闭环反馈）。
v2: 提供 AgentContext 驱动的 evaluate_v2()，返回 Pydantic 模型。

输出结构（对齐 docs/design.md §10.4.3）:
    overall_score: float           — 综合评分 0-100
    dimensions: list[dict]         — 各维度评分
        name: str                  — 维度名称
        score: float               — 0-100
        comment: str               — 评价
    weak_topics: list[str]         — 薄弱知识点列表
    suggestions: list[str]         — 改进建议
    review_plan: list[dict]        — 复习推送计划（创新点：遗忘曲线驱动）
        topic: str                 — 待复习知识点
        urgency: str               — high | medium | low
        reason: str                — 推送原因
        recommended_resources: list[str] — 推荐复习资源类型
"""
import json
import logging
import math
from datetime import datetime, timezone
from typing import Optional, List, Dict

from .base_agent import BaseAgent
from core.agent_context import AgentContext
from agents.schemas import EvaluationOutput, EvalDataSummary, EvalOverall, EvalDimensions, WeaknessDetail
from agents.prompts.evaluation_prompts import EVALUATE_SYSTEM_PROMPT

try:
    from config import LLM_STRICT_MODE
except ModuleNotFoundError:
    from backend.config import LLM_STRICT_MODE

logger = logging.getLogger(__name__)


class EvaluateAgent(BaseAgent):
    """学习效果评估 + 遗忘曲线驱动的间隔复习"""

    def __init__(self, llm_client=None):
        super().__init__(llm_client)
        # 艾宾浩斯遗忘曲线参数
        self._memory_decay_threshold = 0.6  # 记忆保留率低于此值触发复习

    def get_system_prompt(self) -> str:
        """返回标准化评估提示词（由 prompts 模块统一管理）。"""
        return EVALUATE_SYSTEM_PROMPT

    # ------------------------------------------------------------------
    # 同步入口（供 service 层同步端点使用）
    # ------------------------------------------------------------------
    def evaluate_sync(
        self,
        student_id: str,
        profile: dict,
        records: List[dict],
        path: Optional[dict] = None,
        context: Optional[AgentContext] = None,
    ) -> str:
        """同步评估（规则化，不依赖 LLM）。

        供 EvaluateService.build_report() 等同步端点调用，
        直接使用统计规则生成评估报告。

        Args:
            student_id: 学生 ID
            profile: 学生画像 dict
            records: 学习记录列表
            path: 当前学习路径
            context: 可选 AgentContext；未提供时自动构造
        """
        if context is None:
            course_id = "default"
            course_id = _extract_course_id(profile, course_id)
            context = AgentContext(user_id=student_id, course_id=course_id)
        logger.info(
            "[EvaluateAgent] evaluate_sync user_id=%s course_id=%s",
            context.user_id, context.course_id,
        )
        return self._rule_based_evaluate(student_id, profile, records, path)

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    async def evaluate(
        self,
        student_id: str,
        profile: dict,
        records: List[dict],
        path: Optional[dict] = None,
        context: Optional[AgentContext] = None,
    ) -> str:
        """
        生成学习评估报告。

        Args:
            student_id: 学生 ID
            profile: 学生画像 dict
            records: 学习记录列表（LearningRecord）
            path: 当前学习路径 dict（含 stages）
            context: 可选 AgentContext；未提供时自动构造
        Returns:
            JSON 字符串: {overall_score, dimensions, weak_topics, suggestions, review_plan}
        """
        if context is None:
            course_id = "default"
            course_id = _extract_course_id(profile, course_id)
            context = AgentContext(user_id=student_id, course_id=course_id)
        logger.info(
            "[EvaluateAgent] evaluate user_id=%s course_id=%s",
            context.user_id, context.course_id,
        )

        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
        records_json = json.dumps(records, ensure_ascii=False, indent=2)
        path_json = json.dumps(path or {}, ensure_ascii=False, indent=2)

        user_prompt = (
            f"学生ID: {student_id}\n"
            f"学生画像:\n{profile_json}\n\n"
            f"学习记录:\n{records_json}\n\n"
            + (f"当前学习路径:\n{path_json}\n\n" if path else "")
            + "请根据以上数据生成多维度学习评估报告。"
        )

        if self.llm:
            try:
                chunks = []
                async for chunk in self.call_llm(user_prompt):
                    chunks.append(chunk)
                return "".join(chunks)
            except Exception:
                pass

        return self._rule_based_evaluate(student_id, profile, records, path)

    # ------------------------------------------------------------------
    # v2: AgentContext 驱动的结构化输出
    # ------------------------------------------------------------------
    async def evaluate_v2(
        self,
        *,
        context: AgentContext,
        profile: dict,
        records: list[dict],
        path: dict | None = None,
    ) -> EvaluationOutput:
        """
        生成学习评估报告 —— v2 结构化版本。

        功能：
        - 按 course_id 过滤学习记录
        - 按 task_id 去重
        - 计算综合评分公式：knowledge_mastery × 0.4 + test_accuracy × 0.25
          + task_completion × 0.2 + learning_consistency × 0.15
        - 优先使用 call_llm_json；LLM 不可用时降级到规则评估

        Args:
            context: 统一 Agent 上下文
            profile: 学生画像 dict
            records: 原始学习记录列表
            path: 当前学习路径 dict

        Returns:
            EvaluationOutput: 通过 Pydantic 校验的评估报告
        """
        logger.info(
            "[EvaluateAgent] evaluate_v2 user_id=%s course_id=%s records_count=%d",
            context.user_id, context.course_id, len(records),
        )

        # ---- 1. 按 course_id 过滤 ----
        filtered_records = [
            r for r in records
            if not r.get("course_id") or r.get("course_id") == context.course_id
        ]

        # ---- 2. 按 task_id 去重（同一 task_id 保留最高分记录） ----
        seen_tasks: dict[str, dict] = {}
        orphans: list[dict] = []
        for r in filtered_records:
            tid = r.get("task_id", "")
            if not tid:
                orphans.append(r)
                continue
            if tid not in seen_tasks:
                seen_tasks[tid] = r
            else:
                existing_score = seen_tasks[tid].get("score", 0) or 0
                current_score = r.get("score", 0) or 0
                if current_score > existing_score:
                    seen_tasks[tid] = r
        deduped_records = list(seen_tasks.values()) + orphans

        logger.info(
            "[EvaluateAgent] evaluate_v2 user_id=%s course_id=%s filtered=%d deduped=%d",
            context.user_id, context.course_id, len(filtered_records), len(deduped_records),
        )

        # ---- 3. 构建 LLM user prompt ----
        profile_inner = profile.get("profile", profile)
        profile_json = json.dumps(profile_inner, ensure_ascii=False, indent=2)
        records_json = json.dumps(deduped_records, ensure_ascii=False, indent=2)
        path_json = json.dumps(path or {}, ensure_ascii=False, indent=2)

        user_prompt = (
            f"课程ID: {context.course_id}\n"
            f"学生画像:\n{profile_json}\n\n"
            f"学习记录 (已去重，仅含当前课程):\n{records_json}\n\n"
            + (f"当前学习路径:\n{path_json}\n\n" if path else "")
            + "请根据以上数据生成多维度学习评估报告。"
        )

        # ---- 4. 尝试 LLM 结构化调用 ----
        try:
            result = await self.call_llm_json(
                context=context,
                user_prompt=user_prompt,
                response_model=EvaluationOutput,
            )
            logger.info(
                "[EvaluateAgent] evaluate_v2 LLM success user_id=%s course_id=%s score=%d",
                context.user_id, context.course_id, result.overall.score,
            )
            return result
        except Exception as e:
            logger.warning(
                "[EvaluateAgent] evaluate_v2 LLM failed user_id=%s course_id=%s: %s",
                context.user_id, context.course_id, e,
            )
            if LLM_STRICT_MODE:
                raise

        # ---- 5. 降级：规则化评估 ----
        logger.info(
            "[EvaluateAgent] evaluate_v2 falling back to rule-based user_id=%s course_id=%s",
            context.user_id, context.course_id,
        )
        return self._rule_based_evaluate_v2(
            context=context,
            profile=profile,
            records=deduped_records,
            path=path,
        )

    def _rule_based_evaluate_v2(
        self,
        context: AgentContext,
        profile: dict,
        records: list[dict],
        path: dict | None = None,
    ) -> EvaluationOutput:
        """
        基于统计规则的评估 —— v2 版本，返回 EvaluationOutput Pydantic 模型。

        镜像 _rule_based_evaluate 的计算逻辑，但输出结构化 Pydantic 模型，
        并支持 course-scoped 过滤（records 应在调用方完成过滤）。
        """
        profile_inner = profile.get("profile", profile)

        now = datetime.now(timezone.utc)

        # --- 从 records 中提取统计 ---
        total_actions = len(records)
        score_records = [r for r in records if r.get("score") is not None]
        avg_score = (
            sum(r.get("score", 0) for r in score_records) / len(score_records) * 100
            if score_records else 50
        )

        # 学习进度: 基于完成/总阶段
        total_stages = len(path.get("stages", [])) if path else 4
        completed_topics = set(
            r.get("topic", "") for r in records if r.get("action") == "complete"
        )
        progress = min(1.0, len(completed_topics) / max(total_stages, 1))

        # 薄弱点: 从低分记录中提取
        weak = [
            r.get("topic", "未知")
            for r in score_records
            if r.get("score", 0) < 0.6
        ]
        weak_topics = list(set(weak)) if weak else []

        # 学习效率: 知识点/小时
        time_values = [(r.get("time_spent") or 0) for r in records]
        total_hours = sum(t for t in time_values if isinstance(t, (int, float))) / 3600 or 0.1
        efficiency = len(completed_topics) / max(total_hours, 0.1)

        # 维度评分
        knowledge_mastery = round(max(0, min(avg_score, 100)))
        test_accuracy = knowledge_mastery
        task_completion = round(max(0, min(progress * 100, 100)))
        active_days = len({
            r.get("created_at", "")[:10]
            for r in records
            if r.get("created_at")
        })
        learning_consistency = round(max(0, min((active_days / 7) * 100, 100)))

        # 综合评分公式
        overall_score = round(
            knowledge_mastery * 0.4
            + test_accuracy * 0.25
            + task_completion * 0.2
            + learning_consistency * 0.15
        )

        dimensions = EvalDimensions(
            knowledge_mastery=knowledge_mastery,
            test_accuracy=test_accuracy,
            task_completion=task_completion,
            learning_consistency=learning_consistency,
        )

        # --- 按 topic 聚合得分（用于 strengths / weaknesses） ---
        topic_scores: dict[str, list[float]] = {}
        for r in score_records:
            topic = r.get("topic", "")
            if topic:
                topic_scores.setdefault(topic, []).append(r.get("score", 0))

        # --- 改进建议 ---
        suggestions: list[str] = []
        if avg_score < 70:
            suggestions.append("建议回顾课堂笔记和教材相关章节，重点理解核心概念")
        if progress < 0.4:
            suggestions.append("当前进度偏慢，建议每天固定 1-2 小时学习时间")
        if efficiency < 1.5:
            suggestions.append("尝试用思维导图整理知识点，提升理解和记忆效率")
        if len(weak_topics) > 2:
            real_weak_list = [t for t in weak_topics if t != "未知"]
            if real_weak_list:
                suggestions.append(f"薄弱知识点较多 ({', '.join(real_weak_list[:3])})，建议逐个攻克而非跳跃学习")
        if not suggestions:
            suggestions.append("继续保持当前学习节奏，可以尝试挑战更高难度的练习")

        # --- strengths：高正确率 topic ---
        strengths = []
        for index, (topic, scores) in enumerate(topic_scores.items()):
            if scores and (sum(scores) / len(scores)) >= 0.8:
                strengths.append({
                    "knowledge_point_id": f"kp_{index}",
                    "name": topic,
                    "score": round(sum(scores) / len(scores) * 100 if scores and max(scores) <= 1 else sum(scores) / len(scores)),
                })
        strengths = strengths[:3]

        # --- weaknesses：低分 topic ---
        real_weak_topics = [t for t in weak_topics if t not in ("暂未检测到明显薄弱点", "未知")]
        weaknesses = []
        for index, topic in enumerate(real_weak_topics[:5]):
            kp_scores = topic_scores.get(topic, [])
            avg_topic_score = int(sum(kp_scores) / len(kp_scores) * 100) if kp_scores else 50
            priority = "high" if index == 0 else "medium"
            weaknesses.append(WeaknessDetail(
                knowledge_point_id=f"kp_weak_{index}",
                name=topic,
                score=min(avg_topic_score, 100),
                priority=priority,
                evidence=["低分记录中多次出现该知识点"],
                recommended_actions=[
                    {"type": "exercise", "title": f"{topic}专项练习", "estimated_minutes": 20},
                    {"type": "document", "title": f"复习{topic}讲义", "estimated_minutes": 15},
                ],
            ))

        # --- 遗忘曲线复习计划 ---
        review_plan = self._compute_review_plan(
            profile_inner, records, weak_topics
        )

        # --- path_adjustments ---
        path_adjustments = []
        for index, topic in enumerate(real_weak_topics[:3]):
            path_adjustments.append({
                "action": "insert_review_task",
                "stage_id": (path or {}).get("current_stage"),
                "knowledge_point_id": f"kp_weak_{index}",
                "reason": f"{topic} 掌握度偏低",
            })

        # --- 数据摘要 ---
        data_summary = EvalDataSummary(
            unique_tasks_completed=len(completed_topics),
            questions_answered=len(score_records),
            tests_completed=len([r for r in records if r.get("action") == "self_eval"]),
            wrongbook_reviews=len([r for r in records if r.get("action") == "review"]),
            learning_minutes=round(sum(time_values) / 60),
        )

        # --- 综合评分 ---
        overall = EvalOverall(
            score=overall_score,
            previous_score=None,
            score_delta=None,
            confidence=0.45 if len(records) < 10 else 0.75,
            level="基础掌握" if overall_score >= 60 else "需要补强",
            short_term_trend="insufficient_data",
            long_term_trend="insufficient_data",
        )

        evaluation_id = f"eval_{context.user_id}_{int(now.timestamp())}"

        logger.info(
            "[EvaluateAgent] _rule_based_evaluate_v2 user_id=%s course_id=%s overall_score=%d",
            context.user_id, context.course_id, overall_score,
        )

        return EvaluationOutput(
            evaluation_id=evaluation_id,
            user_id=context.user_id,
            course_id=context.course_id,
            scope={
                "type": "current_input",
                "start_at": None,
                "end_at": now.isoformat(),
            },
            data_summary=data_summary,
            overall=overall,
            dimensions=dimensions,
            strengths=strengths,
            weaknesses=weaknesses,
            summary=suggestions[0] if suggestions else "继续保持当前学习节奏。",
            recommendations=suggestions,
            path_adjustments=path_adjustments,
            profile_updates=[],
            generated_at=now.isoformat(),
        )

    # ------------------------------------------------------------------
    # 规则化兜底（无需 LLM）
    # ------------------------------------------------------------------
    def _rule_based_evaluate(
        self,
        student_id: str,
        profile: dict,
        records: List[dict],
        path: Optional[dict] = None,
    ) -> str:
        """基于统计规则的评估（无需 LLM）"""
        profile_inner = profile.get("profile", profile)

        # --- 从 records 中提取统计 ---
        total_actions = len(records)
        score_records = [r for r in records if r.get("score") is not None]
        avg_score = (
            sum(r.get("score", 0) for r in score_records) / len(score_records) * 100
            if score_records else 50
        )

        # 学习进度: 基于完成/总阶段
        total_stages = len(path.get("stages", [])) if path else 4
        completed_topics = set(
            r.get("topic", "") for r in records if r.get("action") == "complete"
        )
        progress = min(1.0, len(completed_topics) / max(total_stages, 1))

        # 薄弱点: 从低分记录中提取
        weak = [
            r.get("topic", "未知")
            for r in score_records
            if r.get("score", 0) < 0.6
        ]
        weak_topics = list(set(weak)) if weak else []

        # 学习效率: 知识点/小时
        time_values = [(r.get("time_spent") or 0) for r in records]
        total_hours = sum(t for t in time_values if isinstance(t, (int, float))) / 3600 or 0.1
        efficiency = len(completed_topics) / max(total_hours, 0.1)

        knowledge_mastery = round(max(0, min(avg_score, 100)))
        test_accuracy = knowledge_mastery
        task_completion = round(max(0, min(progress * 100, 100)))
        learning_consistency = round(max(0, min((len({r.get("created_at", "")[:10] for r in records if r.get("created_at")}) / 7) * 100, 100)))
        overall_score = round(
            knowledge_mastery * 0.4
            + test_accuracy * 0.25
            + task_completion * 0.2
            + learning_consistency * 0.15
        )
        dimensions = {
            "knowledge_mastery": knowledge_mastery,
            "test_accuracy": test_accuracy,
            "task_completion": task_completion,
            "learning_consistency": learning_consistency,
        }

        # --- 改进建议 ---
        suggestions = []
        if avg_score < 70:
            suggestions.append("建议回顾课堂笔记和教材相关章节，重点理解核心概念")
        if progress < 0.4:
            suggestions.append("当前进度偏慢，建议每天固定 1-2 小时学习时间")
        if efficiency < 1.5:
            suggestions.append("尝试用思维导图整理知识点，提升理解和记忆效率")
        if len(weak_topics) > 2:
            suggestions.append(f"薄弱知识点较多 ({', '.join(weak_topics[:3])})，建议逐个攻克而非跳跃学习")
        if not suggestions:
            suggestions.append("继续保持当前学习节奏，可以尝试挑战更高难度的练习")

        # --- 遗忘曲线复习计划 ---
        review_plan = self._compute_review_plan(
            profile_inner, records, weak_topics
        )

        now = datetime.now(timezone.utc)
        real_weak_topics = [t for t in weak_topics if t != "未知"]
        result = {
            "evaluation_id": f"eval_{student_id}_{int(now.timestamp())}",
            "user_id": profile_inner.get("user_id"),
            "student_id": student_id,
            "course_id": profile_inner.get("course_id"),
            "course_name": profile_inner.get("learning_goal") or profile_inner.get("course_name") or "当前课程",
            "stage_id": (path or {}).get("current_stage"),
            "scope": {
                "type": "current_input",
                "start_at": None,
                "end_at": now.isoformat(),
            },
            "data_summary": {
                "unique_tasks_completed": len(completed_topics),
                "questions_answered": len(score_records),
                "tests_completed": len([r for r in records if r.get("action") == "self_eval"]),
                "wrongbook_reviews": len([r for r in records if r.get("action") == "review"]),
                "learning_minutes": round(sum(time_values) / 60),
            },
            "overall": {
                "score": overall_score,
                "previous_score": None,
                "score_delta": 0,
                "period_average": overall_score,
                "confidence": 0.45 if len(records) < 10 else 0.75,
                "level": "基础掌握" if overall_score >= 60 else "需要补强",
                "short_term_trend": "insufficient_data",
                "long_term_trend": "insufficient_data",
            },
            "dimensions": dimensions,
            "strengths": [],
            "weaknesses": [
                {
                    "knowledge_point_id": f"kp_weak_{index}",
                    "name": topic,
                    "score": 50,
                    "priority": "high" if index == 0 else "medium",
                    "evidence": ["低分记录中多次出现该知识点"],
                    "actions": [
                        {"type": "exercise", "title": f"{topic}专项练习", "estimated_minutes": 20},
                        {"type": "document", "title": f"复习{topic}讲义", "estimated_minutes": 15},
                    ],
                }
                for index, topic in enumerate(real_weak_topics[:5])
            ],
            "summary": suggestions[0] if suggestions else "继续保持当前学习节奏。",
            "path_adjustments": [
                {
                    "action": "insert_review_task",
                    "stage_id": (path or {}).get("current_stage"),
                    "knowledge_point_id": f"kp_weak_{index}",
                    "reason": f"{topic} 掌握度偏低",
                }
                for index, topic in enumerate(real_weak_topics[:3])
            ],
            "review_plan": review_plan,
            "generated_at": now.isoformat(),
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 遗忘曲线计算（创新点）
    # ------------------------------------------------------------------
    def _compute_review_plan(
        self,
        profile: dict,
        records: List[dict],
        weak_topics: List[str],
    ) -> List[dict]:
        """
        基于艾宾浩斯遗忘曲线 R = e^(-t/S) 计算复习推送。

        Args:
            profile: 学生画像（含 memory_strength）
            records: 学习记录
            weak_topics: 已识别的薄弱点
        Returns:
            review_plan: [{topic, urgency, reason, recommended_resources}]
        """
        # 解析已有的记忆强度数据
        memory_strength = {}
        raw = profile.get("memory_strength")
        if raw:
            try:
                memory_strength = json.loads(raw) if isinstance(raw, str) else raw
            except (json.JSONDecodeError, TypeError):
                memory_strength = {}

        # 从 records 更新各 topic 的最后学习时间和正确率
        topic_last_time = {}
        topic_scores = {}
        now = datetime.now(timezone.utc)

        for r in records:
            topic = r.get("topic", "")
            if not topic:
                continue
            created = r.get("created_at")
            if created:
                if isinstance(created, str):
                    try:
                        created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        if created.tzinfo is None:
                            created = created.replace(tzinfo=timezone.utc)
                    except (ValueError, AttributeError):
                        created = now
                if topic not in topic_last_time or created > topic_last_time[topic]:
                    topic_last_time[topic] = created

            score = r.get("score")
            if score is not None:
                if topic not in topic_scores:
                    topic_scores[topic] = []
                topic_scores[topic].append(score)

        # 更新 S（记忆强度）并为每个 topic 计算 R
        plan = []
        for topic, last_time in topic_last_time.items():
            # 距上次学习的时间（天）
            t = (now - last_time).total_seconds() / 86400.0

            # 记忆强度 S: 初始 7，正确率加权调整
            scores = topic_scores.get(topic, [])
            avg = sum(scores) / len(scores) if scores else 0.7
            S = memory_strength.get(topic, 7.0)
            # 得分高 → S 增大（记忆更牢固）；得分低 → S 减小
            S = max(1.0, S * (0.5 + avg))  # S ∈ [1.0, …]

            # 艾宾浩斯公式
            R = math.exp(-t / max(S, 0.01))
            memory_strength[topic] = round(S, 2)

            if R < self._memory_decay_threshold:
                urgency = "high" if R < 0.35 else "medium" if R < 0.5 else "low"
                plan.append({
                    "topic": topic,
                    "urgency": urgency,
                    "reason": (
                        f"距上次学习已过 {t:.0f} 天，记忆保留率约 {R:.1%}，"
                        f"低于阈值 {self._memory_decay_threshold:.0%}，建议复习"
                    ),
                    "recommended_resources": ["document", "exercise"],
                })

        # 薄弱点即使 R 不低也应出现在复习计划中
        for wt in weak_topics:
            if wt and wt not in {p["topic"] for p in plan}:
                plan.append({
                    "topic": wt,
                    "urgency": "medium",
                    "reason": "练习正确率偏低，属于薄弱知识点",
                    "recommended_resources": ["exercise", "document"],
                })

        return sorted(plan, key=lambda p: {"high": 0, "medium": 1, "low": 2}[p["urgency"]])

    # ------------------------------------------------------------------
    # 辅助: 根据记录计算记忆强度（供外部调用）
    # ------------------------------------------------------------------
    @staticmethod
    def compute_memory_strength(records: List[dict]) -> dict:
        """
        根据学习记录批量计算所有知识点的记忆强度。
        可用于更新 student_profiles.memory_strength 字段。

        Returns:
            {topic: strength_float, ...}
        """
        evaluator = EvaluateAgent()
        topic_data = {}
        now = datetime.now(timezone.utc)

        for r in records:
            topic = r.get("topic", "")
            if not topic:
                continue
            if topic not in topic_data:
                topic_data[topic] = {"scores": [], "last_time": None}

            score = r.get("score")
            if score is not None:
                topic_data[topic]["scores"].append(score)

            created = r.get("created_at")
            if created:
                if isinstance(created, str):
                    try:
                        created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        if created.tzinfo is None:
                            created = created.replace(tzinfo=timezone.utc)
                    except (ValueError, AttributeError):
                        created = now
                if (
                    topic_data[topic]["last_time"] is None
                    or created > topic_data[topic]["last_time"]
                ):
                    topic_data[topic]["last_time"] = created

        result = {}
        for topic, data in topic_data.items():
            scores = data["scores"]
            avg = sum(scores) / len(scores) if scores else 0.7
            result[topic] = round(max(1.0, 7.0 * (0.5 + avg)), 2)

        return result


# ------------------------------------------------------------------
# 模块级辅助函数
# ------------------------------------------------------------------
def _extract_course_id(profile: dict, default: str = "default") -> str:
    """从 profile dict 中提取 course_id。"""
    if not isinstance(profile, dict):
        return default
    inner = profile.get("profile", profile)
    if isinstance(inner, dict):
        return inner.get("course_id", default)
    return default
