-- ============================================================
-- EduAgent 初始测试数据
-- 用于开发联调和测试，包含 3 个典型学生场景
-- ============================================================

-- ============================================================
-- 1. 学生表 (students)
-- ============================================================
INSERT INTO students (id, nickname, created_at, updated_at) VALUES
('stu_001', '小张', '2026-06-01 08:00:00', '2026-06-10 10:30:00'),
('stu_002', '小李', '2026-06-02 09:00:00', '2026-06-11 14:20:00'),
('stu_003', '小王', '2026-06-03 10:00:00', '2026-06-12 16:45:00');

-- ============================================================
-- 2. 学生画像表 (student_profiles)
-- ============================================================

-- 学生1：小张 — 零基础入门型（文科转专业，数学弱，偏好视频学习）
INSERT INTO student_profiles (student_id, version, knowledge_level, learning_goal, learning_history, cognitive_style, weakness, interest, memory_strength, completeness, created_at) VALUES
('stu_001', 1,
 '初级（大二），Python入门，数学基础薄弱——高数遗忘、未学线代/概率',
 '跟上人工智能导论课程进度，考试及格',
 '["学过大学计算机基础","会Python基本语法","对AI零了解"]',
 '视觉型（偏好视频/图解），不偏好阅读文本',
 '["计算机基础","编程能力","数学基础（高数、线代、概率论）"]',
 '["计算机视觉（人脸识别）","语音识别（智能音箱）"]',
 '{"线性代数":0.3,"概率论":0.2,"Python基础":0.6}',
 0.80,
 '2026-06-10 10:30:00');

-- 学生2：小李 — 编程转AI型（计算机科班，数学推导弱，偏好代码）
INSERT INTO student_profiles (student_id, version, knowledge_level, learning_goal, learning_history, cognitive_style, weakness, interest, memory_strength, completeness, created_at) VALUES
('stu_002', 1,
 '中高级（大三计算机），Java/Python熟练，ML概念有科普级了解，数学推导偏弱',
 '6个月内系统掌握ML/DL核心算法，Kaggle参赛，重点NLP方向',
 '["学过数据结构与算法","Java/Python项目经验丰富","有规则聊天机器人项目"]',
 '动手型（偏好代码实现，从代码反推理论）',
 '["数学推导（微积分/线代应用）","ML算法数学原理"]',
 '["NLP","大语言模型","对话系统","Kaggle竞赛","图神经网络"]',
 '{"线性代数":0.7,"概率论":0.8,"Python":0.95,"机器学习基础":0.4}',
 0.85,
 '2026-06-11 14:20:00');

-- 学生3：小王 — 跨专业应用型（生物信息学研一，统计好，需针对性路径）
INSERT INTO student_profiles (student_id, version, knowledge_level, learning_goal, learning_history, cognitive_style, weakness, interest, memory_strength, completeness, created_at) VALUES
('stu_003', 1,
 '中高级（研一生物信息学），统计扎实，R熟练，Python中等，CNN有基础，GNN薄弱',
 '3个月内（每周15h）：系统性补ML/DL基础 -> GNN -> 蛋白质结构预测应用',
 '["统计学基础扎实","R语言熟练","Python中等水平","读过AlphaFold论文"]',
 '动手+理论混合型（论文+代码学习，需结构化路径）',
 '["Python编程深度","图神经网络（GNN）","ML/DL系统性基础"]',
 '["蛋白质结构预测","图神经网络","AlphaFold","Transformer","蛋白质语言模型（ESM）"]',
 '{"统计学":0.95,"R语言":0.9,"Python":0.65,"CNN":0.5,"GNN":0.2}',
 0.85,
 '2026-06-12 16:45:00');

-- ============================================================
-- 3. 学习路径表 (learning_paths)
-- ============================================================

-- 学生1 的路径：5阶段基础入门
INSERT INTO learning_paths (student_id, version, goal, stages, current_stage, status) VALUES
('stu_001', 1,
 '跟上人工智能导论课程进度，考试及格',
 '[
   {"stage_id":1,"title":"计算机基础补强","estimated_days":4,"difficulty":"初级"},
   {"stage_id":2,"title":"Python编程入门","estimated_days":5,"difficulty":"初级"},
   {"stage_id":3,"title":"数学基础","estimated_days":6,"difficulty":"初级"},
   {"stage_id":4,"title":"AI核心概念","estimated_days":7,"difficulty":"中级"},
   {"stage_id":5,"title":"综合实战：人脸识别小项目","estimated_days":5,"difficulty":"中级"}
 ]',
 1, 'active');

-- 学生2 的路径：4阶段快速进阶
INSERT INTO learning_paths (student_id, version, goal, stages, current_stage, status) VALUES
('stu_002', 1,
 '6个月内系统掌握ML/DL核心算法，Kaggle参赛',
 '[
   {"stage_id":1,"title":"数学推导强化","estimated_days":7,"difficulty":"中级"},
   {"stage_id":2,"title":"经典ML算法深入","estimated_days":14,"difficulty":"中高级"},
   {"stage_id":3,"title":"深度学习与NLP","estimated_days":21,"difficulty":"高级"},
   {"stage_id":4,"title":"Kaggle实战与模型部署","estimated_days":14,"difficulty":"高级"}
 ]',
 1, 'active');

-- 学生3 的路径：5阶段聚焦路径
INSERT INTO learning_paths (student_id, version, goal, stages, current_stage, status) VALUES
('stu_003', 1,
 '3个月内：补ML/DL必要基础 -> 深入掌握GNN -> 应用于蛋白质结构预测',
 '[
   {"stage_id":1,"title":"Python编程强化","estimated_days":5,"difficulty":"中级"},
   {"stage_id":2,"title":"ML/DL系统基础","estimated_days":14,"difficulty":"中级"},
   {"stage_id":3,"title":"图神经网络专攻","estimated_days":21,"difficulty":"高级"},
   {"stage_id":4,"title":"蛋白质结构预测实战","estimated_days":21,"difficulty":"高级"},
   {"stage_id":5,"title":"综合项目：蛋白质-配体相互作用预测","estimated_days":14,"difficulty":"高级"}
 ]',
 1, 'active');

-- ============================================================
-- 4. 学习资源表 (resources)
-- ============================================================

-- 学生1 的资源
INSERT INTO resources (student_id, path_id, type, title, content, topic, difficulty, is_review) VALUES
('stu_001', 1, 'document', '计算机基础入门', '## 计算机基础入门\n\n### 操作系统基础\n...\n\n### 文件系统\n...', '计算机基础', '初级', 0),
('stu_001', 1, 'video',   'Python入门教程', 'https://example.com/python-intro', 'Python基础', '初级', 0),
('stu_001', 1, 'exercise','Python基础练习', '# Python练习\n\n1. 写一个函数计算斐波那契数列...', 'Python基础', '初级', 0),
('stu_001', 1, 'mindmap', 'AI知识图谱', '- AI\n  - 机器学习\n    - 监督学习\n    - 无监督学习\n  - 深度学习\n    - CNN\n    - RNN', 'AI概论', '初级', 0);

-- 学生2 的资源
INSERT INTO resources (student_id, path_id, type, title, content, topic, difficulty, is_review) VALUES
('stu_002', 2, 'document', '线性代数复习笔记', '## 线性代数在ML中的应用\n\n### 矩阵分解\n...', '线性代数', '中级', 0),
('stu_002', 2, 'code',     'SVM从零实现', '```python\nimport numpy as np\n\nclass SVM:\n    def __init__(self):\n        ...\n```', '支持向量机', '中高级', 0),
('stu_002', 2, 'reading',  'Attention Is All You Need 论文导读', '## 论文核心贡献\n\nTransformer架构的提出...', 'Transformer', '高级', 0);

-- 学生3 的资源
INSERT INTO resources (student_id, path_id, type, title, content, topic, difficulty, is_review) VALUES
('stu_003', 3, 'code',     'PyTorch基础教程', '```python\nimport torch\nimport torch.nn as nn\n\n# 定义一个简单的网络\nmodel = nn.Sequential(\n    nn.Linear(10, 20),\n    nn.ReLU(),\n    nn.Linear(20, 1)\n)\n```', 'PyTorch', '中级', 0),
('stu_003', 3, 'document', '图神经网络综述', '## GNN基础\n\n### 消息传递框架\n...\n\n### GCN/GAT/GraphSAGE对比', '图神经网络', '高级', 0),
('stu_003', 3, 'document', '蛋白质结构预测方法', '## AlphaFold简介\n\n### 输入与输出\n...', '蛋白质结构预测', '高级', 0);

-- ============================================================
-- 5. 学习记录表 (learning_records)
-- ============================================================

-- 学生1 的学习记录
INSERT INTO learning_records (student_id, resource_id, action, topic, score, time_spent) VALUES
('stu_001', 1, 'view',     '计算机基础', NULL, 1200),
('stu_001', 1, 'complete', '计算机基础', 0.75, 3600),
('stu_001', 2, 'view',     'Python基础',  NULL, 900),
('stu_001', 3, 'answer',   'Python基础',  0.60, 1800);

-- 学生2 的学习记录
INSERT INTO learning_records (student_id, resource_id, action, topic, score, time_spent) VALUES
('stu_002', 5, 'view',     '线性代数', NULL, 2400),
('stu_002', 5, 'complete', '线性代数', 0.90, 5400),
('stu_002', 6, 'view',     '支持向量机', NULL, 1800),
('stu_002', 6, 'answer',   '支持向量机', 0.85, 3600),
('stu_002', 7, 'view',     'Transformer', NULL, 3600);

-- 学生3 的学习记录
INSERT INTO learning_records (student_id, resource_id, action, topic, score, time_spent) VALUES
('stu_003', 8, 'view',     'PyTorch', NULL, 1800),
('stu_003', 8, 'complete', 'PyTorch', 0.80, 4800),
('stu_003', 9, 'view',     '图神经网络', NULL, 3600);
