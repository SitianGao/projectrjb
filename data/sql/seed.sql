-- ============================================================
-- EduAgent initial demo data
-- Run after data/sql/schema.sql. All primary keys are explicit
-- so the script works with the SQLAlchemy models.
-- ============================================================

PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO students (id, nickname, created_at, updated_at) VALUES
('demo-student-01', '演示学生', '2026-06-12 08:00:00', '2026-06-18 10:30:00'),
('stu_001', '小张', '2026-06-01 08:00:00', '2026-06-10 10:30:00'),
('stu_002', '小李', '2026-06-02 09:00:00', '2026-06-11 14:20:00'),
('stu_003', '小王', '2026-06-03 10:00:00', '2026-06-12 16:45:00');

INSERT OR IGNORE INTO student_profiles (
    id, student_id, version, knowledge_level, learning_goal, learning_history,
    cognitive_style, pace_preference, weakness, interest, memory_strength,
    completeness, created_at, updated_at
) VALUES
('profile_demo_001', 'demo-student-01', 1,
 '中级，具备 Python 基础，正在系统学习机器学习和深度学习',
 '完成机器学习基础、深度学习入门和 NLP 复习，形成可持续复习计划',
 '["完成 Python 基础练习","阅读过机器学习入门材料","做过线性回归和梯度下降练习"]',
 '动手型学习者，偏好代码示例和结构化总结',
 '中速均衡型',
 '["梯度下降细节","神经网络反向传播","概率统计基础"]',
 '["机器学习","深度学习","自然语言处理"]',
 '{"线性回归":8.5,"梯度下降":4.5,"神经网络基础":5.5}',
 0.86,
 '2026-06-18 09:30:00', '2026-06-18 09:30:00'),
('profile_stu_001', 'stu_001', 1,
 '初级，Python 入门，数学基础薄弱',
 '跟上人工智能导论课程进度，考试及格',
 '["学过大学计算机基础","会 Python 基本语法","对 AI 零了解"]',
 '视觉型学习者，偏好视频和图解',
 '慢速深入型',
 '["计算机基础","编程能力","数学基础"]',
 '["计算机视觉","语音识别"]',
 '{"线性代数":3.0,"概率论":2.0,"Python基础":6.0}',
 0.80,
 '2026-06-10 10:30:00', '2026-06-10 10:30:00'),
('profile_stu_002', 'stu_002', 1,
 '中高级，计算机基础扎实，数学推导偏弱',
 '6 个月内系统掌握 ML/DL 核心算法，参加 Kaggle',
 '["学过数据结构与算法","有 Python 项目经验","了解 ML 基础概念"]',
 '动手型学习者，偏好从代码反推理论',
 '快速概览型',
 '["数学推导","ML 算法数学原理"]',
 '["NLP","大语言模型","Kaggle竞赛"]',
 '{"线性代数":7.0,"概率论":8.0,"Python":9.5,"机器学习基础":4.0}',
 0.85,
 '2026-06-11 14:20:00', '2026-06-11 14:20:00'),
('profile_stu_003', 'stu_003', 1,
 '中高级，统计扎实，Python 中等，GNN 薄弱',
 '3 个月内补 ML/DL 基础并应用到蛋白质结构预测',
 '["统计学基础扎实","R 语言熟练","读过 AlphaFold 论文"]',
 '动手+理论混合型，偏好论文配代码',
 '中速均衡型',
 '["Python 编程深度","图神经网络","ML/DL 系统基础"]',
 '["蛋白质结构预测","图神经网络","Transformer"]',
 '{"统计学":9.5,"R语言":9.0,"Python":6.5,"CNN":5.0,"GNN":2.0}',
 0.85,
 '2026-06-12 16:45:00', '2026-06-12 16:45:00');

INSERT OR IGNORE INTO learning_paths (
    id, student_id, version, goal, stages, current_stage, status, created_at, updated_at
) VALUES
('path_demo_001', 'demo-student-01', 1,
 '完成机器学习基础、深度学习入门和 NLP 复习',
 '[
   {"stage_id":1,"title":"机器学习基础巩固","description":"复习线性回归、损失函数和模型评估。","objectives":["理解监督学习流程","掌握训练/测试划分"],"topics":["线性回归","模型评估"],"estimated_days":3,"difficulty":"中级","tasks":[{"task_id":"demo-1-1","type":"study","description":"阅读机器学习基础讲义","estimated_days":1,"difficulty":"中级","status":"completed"},{"task_id":"demo-1-2","type":"exercise","description":"完成线性回归练习","estimated_days":1,"difficulty":"中级","status":"completed"}]},
   {"stage_id":2,"title":"梯度下降专项","description":"重点补齐梯度下降和参数更新过程。","objectives":["能解释学习率影响","能手写一轮参数更新"],"topics":["梯度下降","学习率"],"estimated_days":4,"difficulty":"中级","tasks":[{"task_id":"demo-2-1","type":"study","description":"复习梯度下降推导","estimated_days":1,"difficulty":"中级","status":"in_progress"},{"task_id":"demo-2-2","type":"exercise","description":"完成梯度下降计算题","estimated_days":1,"difficulty":"中级","status":"pending"}]},
   {"stage_id":3,"title":"深度学习入门","description":"学习神经网络、反向传播和 PyTorch 基础。","objectives":["理解神经元和激活函数","能运行 PyTorch 示例"],"topics":["神经网络基础","PyTorch"],"estimated_days":5,"difficulty":"中级","tasks":[{"task_id":"demo-3-1","type":"study","description":"阅读神经网络基础材料","estimated_days":2,"difficulty":"中级","status":"pending"}]}
 ]',
 2, 'active', '2026-06-18 09:40:00', '2026-06-18 09:40:00'),
('path_stu_001', 'stu_001', 1,
 '跟上人工智能导论课程进度，考试及格',
 '[{"stage_id":1,"title":"计算机基础补强","estimated_days":4,"difficulty":"初级"},{"stage_id":2,"title":"Python编程入门","estimated_days":5,"difficulty":"初级"},{"stage_id":3,"title":"数学基础","estimated_days":6,"difficulty":"初级"}]',
 1, 'active', '2026-06-10 11:00:00', '2026-06-10 11:00:00'),
('path_stu_002', 'stu_002', 1,
 '6 个月内系统掌握 ML/DL 核心算法，参加 Kaggle',
 '[{"stage_id":1,"title":"数学推导强化","estimated_days":7,"difficulty":"中级"},{"stage_id":2,"title":"经典 ML 算法深入","estimated_days":14,"difficulty":"高级"}]',
 1, 'active', '2026-06-11 15:00:00', '2026-06-11 15:00:00'),
('path_stu_003', 'stu_003', 1,
 '补 ML/DL 必要基础并深入掌握 GNN',
 '[{"stage_id":1,"title":"Python 编程强化","estimated_days":5,"difficulty":"中级"},{"stage_id":2,"title":"图神经网络专攻","estimated_days":21,"difficulty":"高级"}]',
 1, 'active', '2026-06-12 17:00:00', '2026-06-12 17:00:00');

INSERT OR IGNORE INTO resources (
    id, student_id, path_id, type, title, content, topic, difficulty, is_review, created_at
) VALUES
('res_demo_001', 'demo-student-01', 'path_demo_001', 'document', '机器学习基础复习讲义',
 '## 机器学习基础\n\n监督学习通常包含数据准备、模型训练、验证评估和迭代优化四个步骤。', '机器学习基础', '中级', 0, '2026-06-18 09:45:00'),
('res_demo_002', 'demo-student-01', 'path_demo_001', 'exercise', '梯度下降专项练习',
 '# 梯度下降练习\n\n1. 解释学习率过大和过小的影响。\n2. 给定损失函数，手算一轮参数更新。', '梯度下降', '中级', 1, '2026-06-18 09:46:00'),
('res_demo_003', 'demo-student-01', 'path_demo_001', 'code', 'PyTorch 神经网络入门',
 '```python\nimport torch\nimport torch.nn as nn\nmodel = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 1))\nprint(model)\n```', '神经网络基础', '中级', 0, '2026-06-18 09:47:00'),
('res_stu_001_001', 'stu_001', 'path_stu_001', 'document', '计算机基础入门',
 '## 计算机基础入门\n\n操作系统、文件系统和程序运行基本概念。', '计算机基础', '初级', 0, '2026-06-10 11:10:00'),
('res_stu_002_001', 'stu_002', 'path_stu_002', 'code', 'SVM 从零实现',
 '```python\nclass SVM:\n    pass\n```', '支持向量机', '高级', 0, '2026-06-11 15:10:00'),
('res_stu_003_001', 'stu_003', 'path_stu_003', 'document', '图神经网络综述',
 '## GNN 基础\n\n消息传递框架、GCN、GAT 和 GraphSAGE 对比。', '图神经网络', '高级', 0, '2026-06-12 17:10:00');

INSERT OR IGNORE INTO learning_records (
    id, student_id, resource_id, action, topic, score, time_spent, created_at
) VALUES
('rec_demo_001', 'demo-student-01', 'res_demo_001', 'view', '机器学习基础', NULL, 1200, '2026-06-15 09:00:00'),
('rec_demo_002', 'demo-student-01', 'res_demo_001', 'complete', '机器学习基础', 0.88, 2400, '2026-06-15 09:30:00'),
('rec_demo_003', 'demo-student-01', 'res_demo_002', 'answer', '梯度下降', 0.55, 1800, '2026-06-17 20:00:00'),
('rec_demo_004', 'demo-student-01', 'res_demo_003', 'view', '神经网络基础', NULL, 900, '2026-06-18 08:30:00'),
('rec_demo_005', 'demo-student-01', 'res_demo_003', 'answer', '神经网络基础', 0.68, 1500, '2026-06-18 09:00:00'),
('rec_stu_001_001', 'stu_001', 'res_stu_001_001', 'complete', '计算机基础', 0.75, 3600, '2026-06-10 12:00:00'),
('rec_stu_002_001', 'stu_002', 'res_stu_002_001', 'answer', '支持向量机', 0.85, 3600, '2026-06-11 16:00:00'),
('rec_stu_003_001', 'stu_003', 'res_stu_003_001', 'view', '图神经网络', NULL, 3600, '2026-06-12 18:00:00');
