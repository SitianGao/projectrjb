-- ============================================================
-- EduAgent demo seed data
-- Fixed student for Day11-Day13 end-to-end acceptance.
-- ============================================================

PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO students (
    id,
    nickname
) VALUES (
    'demo-student-01',
    '演示学生'
);

INSERT OR IGNORE INTO student_profiles (
    id,
    student_id,
    version,
    knowledge_level,
    learning_goal,
    learning_history,
    cognitive_style,
    pace_preference,
    weakness,
    interest,
    chat_history,
    memory_strength,
    completeness
) VALUES (
    'profile_demo_student_01',
    'demo-student-01',
    1,
    '中级，具备 Python 基础，正在系统学习机器学习',
    '掌握机器学习基础并补齐梯度下降薄弱点',
    '["完成 Python 基础", "阅读机器学习入门材料"]',
    '动手型学习者',
    '中速均衡型',
    '["梯度下降", "神经网络基础"]',
    '["机器学习", "深度学习", "可视化实验"]',
    '[]',
    '{"线性回归": 8.5, "梯度下降": 4.5, "神经网络": 3.8}',
    0.86
);

INSERT OR IGNORE INTO learning_paths (
    id,
    student_id,
    version,
    goal,
    stages,
    current_stage,
    status
) VALUES (
    'path_demo_student_01',
    'demo-student-01',
    1,
    '完成机器学习基础、梯度下降和神经网络入门',
    '[{"stage_id":1,"title":"机器学习基础巩固","description":"复习监督学习、线性回归和模型评估。","objectives":["理解监督学习流程","掌握训练/测试划分"],"topics":["机器学习基础","线性回归"],"estimated_days":3,"difficulty":"中级","tasks":[{"task_id":"demo-1-1","type":"study","description":"阅读机器学习基础讲义","estimated_days":1,"difficulty":"中级","status":"completed"}]},{"stage_id":2,"title":"梯度下降专项","description":"补齐梯度下降和学习率理解。","objectives":["解释学习率影响","手算一轮参数更新"],"topics":["梯度下降","学习率"],"estimated_days":4,"difficulty":"中级","tasks":[{"task_id":"demo-2-1","type":"exercise","description":"完成梯度下降练习题","estimated_days":1,"difficulty":"中级","status":"pending"}]}]',
    1,
    'active'
);

INSERT OR IGNORE INTO resources (
    id,
    student_id,
    path_id,
    type,
    title,
    content,
    topic,
    difficulty,
    is_review
) VALUES (
    'res_demo_student_01',
    'demo-student-01',
    'path_demo_student_01',
    'document',
    '机器学习基础讲义',
    '## 机器学习基础\n\n监督学习包含数据准备、模型训练、验证评估和迭代优化。梯度下降通过损失函数梯度更新参数，是训练线性模型和神经网络的重要方法。',
    '机器学习基础',
    '中级',
    0
);

INSERT OR IGNORE INTO learning_records (
    id,
    student_id,
    resource_id,
    action,
    topic,
    score,
    time_spent
) VALUES (
    'rec_demo_student_01',
    'demo-student-01',
    'res_demo_student_01',
    'complete',
    '机器学习基础',
    0.88,
    2400
);
