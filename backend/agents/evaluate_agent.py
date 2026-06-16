"""
EvaluateAgent —— 学习效果评估智能体

根据学习记录、练习结果和行为数据，评估学习效果并给出优化建议，
驱动学习路径的动态调整（闭环反馈）。

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
import math
from datetime import datetime, timezone
from typing import Optional, List, Dict

from .base_agent import BaseAgent


class EvaluateAgent(BaseAgent):
    """学习效果评估 + 遗忘曲线驱动的间隔复习"""

    def __init__(self, llm_client=None):
        super().__init__(llm_client)
        # 艾宾浩斯遗忘曲线参数
        self._memory_decay_threshold = 0.6  # 记忆保留率低于此值触发复习

    def get_system_prompt(self) -> str:
        return (
            "你是学习效果评估智能体。\n"
            "根据学生的学习行为记录、练习成绩、资源使用情况，进行多维度评估。\n\n"
            "## 评估维度\n"
            "1. 知识掌握度 (knowledge_mastery): 基于练习得分和正确率\n"
            "2. 学习进度 (progress): 基于已完成阶段数 / 总阶段数\n"
            "3. 学习效率 (efficiency): 基于单位时间掌握的知识点数\n"
            "4. 薄弱点分析 (weakness_analysis): 识别易错和高频错误知识点\n\n"
            "## 防幻觉约束\n"
            "- 评分必须基于实际数据（records），不得凭空打分。\n"
            "- 薄弱点必须来自学生的错题记录，不猜测。\n"
            "- 建议必须具体到知识点级别，泛泛而谈无效。\n\n"
            "## 输出格式\n"
            "严格输出 JSON: {overall_score, dimensions, weak_topics, suggestions, review_plan}"
        )

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    async def evaluate(
        self,
        student_id: str,
        profile: dict,
        records: List[dict],
        path: Optional[dict] = None,
    ) -> str:
        """
        生成学习评估报告。

        Args:
            student_id: 学生 ID
            profile: 学生画像 dict
            records: 学习记录列表（LearningRecord）
            path: 当前学习路径 dict（含 stages）
        Returns:
            JSON 字符串: {overall_score, dimensions, weak_topics, suggestions, review_plan}
        """
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
        weak_topics = list(set(weak)) if weak else ["暂未检测到明显薄弱点"]

        # 学习效率: 知识点/小时
        time_values = [(r.get("time_spent") or 0) for r in records]
        total_hours = sum(t for t in time_values if isinstance(t, (int, float))) / 3600 or 0.1
        efficiency = len(completed_topics) / max(total_hours, 0.1)

        # --- 四维度评分 ---
        dimensions = [
            {
                "name": "knowledge_mastery",
                "score": round(avg_score, 1),
                "comment": (
                    "掌握良好，正确率较高"
                    if avg_score >= 75
                    else "存在知识盲区，建议针对性复习"
                    if avg_score >= 50
                    else "基础薄弱，需要重新巩固核心概念"
                ),
            },
            {
                "name": "progress",
                "score": round(progress * 100, 1),
                "comment": (
                    "进度正常，按计划推进"
                    if progress >= 0.5
                    else "进度偏慢，建议加快学习节奏"
                ),
            },
            {
                "name": "efficiency",
                "score": round(min(efficiency * 100, 100), 1),
                "comment": (
                    "学习效率良好"
                    if efficiency >= 2
                    else "效率偏低，建议优化学习方法"
                ),
            },
            {
                "name": "weakness_analysis",
                "score": round(max(0, 100 - len(weak_topics) * 15), 1),
                "comment": (
                    "无明显薄弱点"
                    if len(weak_topics) <= 1
                    else f"检测到 {len(weak_topics)} 个薄弱知识点，需要加强练习"
                ),
            },
        ]

        # --- 综合评分 ---
        overall_score = round(
            sum(d["score"] for d in dimensions) / len(dimensions), 1
        )

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

        result = {
            "overall_score": overall_score,
            "dimensions": dimensions,
            "weak_topics": weak_topics,
            "suggestions": suggestions,
            "review_plan": review_plan,
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
