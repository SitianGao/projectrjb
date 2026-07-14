"""
演示数据注入脚本 —— 为 review_plan（遗忘曲线驱动复习推送）提供样例数据

用法:
    cd backend
    python ../data/seed_review_demo.py            # 注入数据
    python ../data/seed_review_demo.py --clear     # 清空后重新注入

设计思路:
    模拟一个已学习 30 天的学生，在 5 个知识点上产生不同时间跨度、
    不同正确率的学习记录，从而触发 EvaluateAgent._compute_review_plan()
    的遗忘曲线 + 薄弱点双重检测，产出有区分度的 review_plan。

    预期 review_plan 输出:
        - SVM:        R≈10%, urgency=high   (20天前 + 低正确率)
        - 线性回归:    R≈30%, urgency=high   (14天前)
        - 决策树:      R≈42%, urgency=medium (7天前)
        - 梯度下降:    R≈65%, urgency=low    (3天前 + 薄弱点)
        - 神经网络基础: R≈87%, 不触发          (1天前 + 高正确率)
"""

import argparse
import datetime
import json
import os
import sys
import uuid

# 将 backend 目录加入 path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from database import SessionLocal, init_db
from models import Student, StudentProfile, LearningPath, Resource, LearningRecord, EvaluationReport


# ═══════════════════════════════════════════════════════════════════════
# 演示数据定义
# ═══════════════════════════════════════════════════════════════════════

DEMO_STUDENT_ID = "demo-student-review"
NOW = datetime.datetime.now(datetime.timezone.utc)

# 5 个知识点及其学习轨迹（dates_before_now 天数 + 平均得分）
TOPICS = [
    {
        "topic": "线性回归",
        "records": [
            {"days_ago": 14, "score": 0.80, "action": "complete", "time_spent": 3600},
            {"days_ago": 21, "score": 0.75, "action": "answer",   "time_spent": 1800},
            {"days_ago": 28, "score": 0.65, "action": "view",     "time_spent": 2400},
        ],
    },
    {
        "topic": "梯度下降",
        "records": [
            {"days_ago": 3,  "score": 0.50, "action": "complete", "time_spent": 5400},
            {"days_ago": 10, "score": 0.45, "action": "answer",   "time_spent": 3600},
            {"days_ago": 17, "score": 0.55, "action": "view",     "time_spent": 3000},
        ],
    },
    {
        "topic": "决策树",
        "records": [
            {"days_ago": 7,  "score": 0.90, "action": "complete", "time_spent": 2700},
            {"days_ago": 14, "score": 0.85, "action": "answer",   "time_spent": 1500},
        ],
    },
    {
        "topic": "支持向量机",
        "records": [
            {"days_ago": 20, "score": 0.40, "action": "complete", "time_spent": 7200},
            {"days_ago": 27, "score": 0.35, "action": "answer",   "time_spent": 4200},
            {"days_ago": 34, "score": 0.50, "action": "view",     "time_spent": 3600},
        ],
    },
    {
        "topic": "神经网络基础",
        "records": [
            {"days_ago": 1,  "score": 0.85, "action": "complete", "time_spent": 4800},
            {"days_ago": 5,  "score": 0.80, "action": "answer",   "time_spent": 2400},
            {"days_ago": 8,  "score": 0.90, "action": "view",     "time_spent": 1800},
            {"days_ago": 15, "score": 0.70, "action": "complete", "time_spent": 3600},
        ],
    },
]

# 预计算 memory_strength（以便 _compute_review_plan 读取）
MEMORY_STRENGTH_SEED = {
    "线性回归":   7.8,   # 初始7.0 × (0.5 + avg_score≈0.73) → 偏低
    "梯度下降":   5.0,   # 低正确率 → S 明显偏低
    "决策树":    10.2,   # 高正确率 → S 偏高
    "支持向量机":  4.2,   # 最低正确率
    "神经网络基础": 8.5,   # 高正确率 + 近期活跃
}

LEARNING_PATH_STAGES = [
    {
        "title": "线性回归入门",
        "objectives": "掌握线性回归的基本原理与最小二乘法推导",
        "topics": ["线性回归", "最小二乘法"],
        "tasks": [
            {"task": "推导最小二乘法的解析解", "resource_type": "document", "estimated_hours": 2.0},
            {"task": "用 NumPy 实现一元线性回归", "resource_type": "code", "estimated_hours": 2.0},
        ],
    },
    {
        "title": "梯度下降与优化",
        "objectives": "理解梯度下降的迭代过程和收敛条件",
        "topics": ["梯度下降", "学习率", "随机梯度下降"],
        "tasks": [
            {"task": "实现批量梯度下降并可视化损失曲线", "resource_type": "code", "estimated_hours": 2.5},
            {"task": "对比不同学习率对收敛的影响", "resource_type": "exercise", "estimated_hours": 1.5},
        ],
    },
    {
        "title": "决策树与集成方法",
        "objectives": "理解决策树的划分准则和集成学习的投票机制",
        "topics": ["决策树", "信息增益", "随机森林"],
        "tasks": [
            {"task": "手算信息增益并画出决策树结构", "resource_type": "document", "estimated_hours": 2.0},
            {"task": "使用 sklearn 训练随机森林并调参", "resource_type": "code", "estimated_hours": 2.0},
        ],
    },
    {
        "title": "支持向量机原理",
        "objectives": "掌握 SVM 的最大间隔分类原理和核技巧",
        "topics": ["支持向量机", "核函数", "软间隔"],
        "tasks": [
            {"task": "推导硬间隔 SVM 的对偶问题", "resource_type": "document", "estimated_hours": 3.0},
            {"task": "用不同核函数对比 SVM 分类效果", "resource_type": "code", "estimated_hours": 2.0},
        ],
    },
    {
        "title": "神经网络基础架构",
        "objectives": "理解前馈神经网络的前向传播与反向传播机制",
        "topics": ["神经网络基础", "反向传播", "激活函数"],
        "tasks": [
            {"task": "从零实现一个 3 层 MLP 的反向传播", "resource_type": "code", "estimated_hours": 3.0},
            {"task": "对比不同激活函数的训练效果", "resource_type": "exercise", "estimated_hours": 1.5},
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════
# 注入逻辑
# ═══════════════════════════════════════════════════════════════════════

def _days_ago(days: int):
    """返回 days 天前的 UTC datetime"""
    return NOW - datetime.timedelta(days=days)


def clear_existing(db):
    """移除已有的演示数据"""
    db.query(LearningRecord).filter(
        LearningRecord.student_id == DEMO_STUDENT_ID
    ).delete()
    db.query(Resource).filter(
        Resource.student_id == DEMO_STUDENT_ID
    ).delete()
    db.query(EvaluationReport).filter(
        EvaluationReport.student_id == DEMO_STUDENT_ID
    ).delete()
    db.query(LearningPath).filter(
        LearningPath.student_id == DEMO_STUDENT_ID
    ).delete()
    db.query(StudentProfile).filter(
        StudentProfile.student_id == DEMO_STUDENT_ID
    ).delete()
    db.query(Student).filter(Student.id == DEMO_STUDENT_ID).delete()
    db.commit()
    print("[clear] 已清理旧演示数据")


def seed(db):
    """注入完整演示数据"""
    _id = lambda: str(uuid.uuid4())

    # ── Student ──
    student = Student(
        id=DEMO_STUDENT_ID,
        nickname="复习演示学生",
    )
    db.add(student)

    # ── StudentProfile ──
    profile = StudentProfile(
        id=_id(),
        student_id=DEMO_STUDENT_ID,
        version=3,
        knowledge_level="中级",
        learning_goal="掌握机器学习核心算法，能够独立完成回归与分类项目",
        cognitive_style="图解型",
        pace_preference="中等节奏",
        weakness=json.dumps(["支持向量机", "梯度下降"], ensure_ascii=False),
        interest=json.dumps(["深度学习", "NLP"], ensure_ascii=False),
        memory_strength=json.dumps(MEMORY_STRENGTH_SEED, ensure_ascii=False),
        completeness=0.72,
    )
    db.add(profile)

    # ── LearningPath ──
    path_id = _id()
    path = LearningPath(
        id=path_id,
        student_id=DEMO_STUDENT_ID,
        version=1,
        goal="掌握机器学习核心算法：线性回归 → 梯度下降 → 决策树 → SVM → 神经网络",
        stages=json.dumps(LEARNING_PATH_STAGES, ensure_ascii=False),
        current_stage=3,
        status="active",
    )
    db.add(path)

    # ── Resources (每个 topic 2-3 份) ──
    resource_templates = [
        ("线性回归", "document", "线性回归 讲解文档", "进阶"),
        ("线性回归", "code",      "线性回归 代码案例", "进阶"),
        ("梯度下降", "document", "梯度下降 讲解文档", "进阶"),
        ("梯度下降", "exercise", "梯度下降 练习题",   "进阶"),
        ("决策树",   "document", "决策树 讲解文档",   "中级"),
        ("决策树",   "code",     "决策树 代码案例",   "中级"),
        ("支持向量机", "document", "支持向量机 讲解文档", "高级"),
        ("支持向量机", "exercise", "支持向量机 练习题",   "高级"),
        ("神经网络基础", "document", "神经网络基础 讲解文档", "中级"),
        ("神经网络基础", "code",     "神经网络基础 代码案例", "中级"),
    ]
    resource_ids: dict[str, list] = {}
    for topic, rtype, title, diff in resource_templates:
        rid = _id()
        resource_ids.setdefault(topic, []).append(rid)
        db.add(Resource(
            id=rid,
            student_id=DEMO_STUDENT_ID,
            path_id=path_id,
            type=rtype,
            title=title,
            content=f"# {title}\n\n（演示内容 —— 实际使用时由 ResourceAgent 生成）\n",
            topic=topic,
            difficulty=diff,
        ))

    # ── LearningRecords (时间跨度的遗忘曲线) ──
    record_count = 0
    for topic_def in TOPICS:
        topic = topic_def["topic"]
        for rec in topic_def["records"]:
            record_count += 1
            db.add(LearningRecord(
                id=_id(),
                student_id=DEMO_STUDENT_ID,
                resource_id=resource_ids.get(topic, [None])[0],
                action=rec["action"],
                topic=topic,
                score=rec["score"],
                time_spent=rec["time_spent"],
                created_at=_days_ago(rec["days_ago"]),
            ))

    db.commit()
    print(f"[seed] 注入完成:")
    print(f"       学生: 1 ({DEMO_STUDENT_ID})")
    print(f"       画像: 1")
    print(f"       学习路径: 1 ({len(LEARNING_PATH_STAGES)} 个阶段)")
    print(f"       资源: {len(resource_templates)}")
    print(f"       学习记录: {record_count} (覆盖 {len(TOPICS)} 个知识点)")

    # ── 预览预期 review_plan ──
    print("\n[preview] 预期遗忘曲线计算结果:")
    from agents.evaluate_agent import EvaluateAgent
    import math

    agent = EvaluateAgent()
    for topic_def in TOPICS:
        topic = topic_def["topic"]
        last_rec = topic_def["records"][0]  # 最新记录
        t = last_rec["days_ago"]
        S = MEMORY_STRENGTH_SEED.get(topic, 7.0)
        R = math.exp(-t / max(S, 0.01))
        weak = "⚠️ 薄弱" if last_rec["score"] < 0.6 else ""
        triggered = "✅ 触发" if R < agent._memory_decay_threshold else "— 不触发"
        urgency = (
            "🔴 high" if R < 0.35 else
            "🟡 medium" if R < 0.5 else
            "🟢 low" if R < agent._memory_decay_threshold else
            "⚪"
        )
        flag = weak if weak else triggered
        print(f"  {topic:　<8s}  t={t:2d}d  S={S:.1f}  R={R:.1%}  {urgency}  {flag}")

    print(f"\n  阈值 R < {agent._memory_decay_threshold:.0%} → 触发复习推送")
    print("  预期 review_plan 含 4 条（神经网络基础不触发）")


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="注入 review_plan 演示数据")
    parser.add_argument("--clear", action="store_true", help="注入前先清空已有演示数据")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        if args.clear:
            clear_existing(db)
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
