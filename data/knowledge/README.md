# EduAgent 知识库索引

> 整理日期：2026-07-03
> 用途：RAG 向量检索的知识源，为 TutorAgent、ResourceAgent 等智能体提供专业背景知识
> RAG 配置：ChromaDB + sentence-transformers (MiniLM-L12-v2, 384-dim)，按 `##`/`###` 分块（800 chars, 100 overlap）
> 仅索引 `.md` 和 `.json` 文件，PDF 不会被向量化

---

## 目录结构

```
data/knowledge/
├── README.md                          # 本索引文件
│
├── 📊 核心算法（顶层）
│   ├── cnn.md                         # 卷积神经网络
│   ├── gradient_descent.md            # 梯度下降算法
│   ├── linear_regression.md           # 线性回归
│   ├── neural_network_basics.md       # 神经网络基础
│   ├── svm.md                         # 支持向量机
│   ├── decision_tree.md               # 决策树与随机森林
│   ├── logistic_regression.md         # 逻辑回归
│   ├── kmeans_clustering.md           # K-Means 聚类
│   ├── naive_bayes.md                 # 朴素贝叶斯
│   ├── ensemble_methods.md            # 集成学习（Bagging/Boosting/Stacking）
│   ├── pca.md                         # 主成分分析与降维
│   ├── rnn_lstm.md                    # RNN / LSTM / GRU 详解
│   ├── transformer_attention.md       # Transformer 与注意力机制
│   ├── gan.md                         # 生成对抗网络
│   └── reinforcement_learning_basics.md # 强化学习基础
│
├── 🛠 实战指南（顶层）
│   ├── data-preprocessing.md          # 数据预处理完整指南
│   ├── model-evaluation.md            # 模型评估指标与方法
│   └── feature-engineering.md         # 特征工程完整指南
│
├── 📚 知识点/
│   ├── ai-fundamentals.md             # 人工智能基础概念
│   ├── ai-algorithms.md               # AI 核心算法总结
│   ├── ai-knowledge-system.md         # AI 知识体系概述
│   ├── ai-review.md                   # AI 综合复习
│   ├── ml_basics.md                   # 机器学习基础
│   ├── ml_advanced.md                 # 机器学习进阶
│   ├── ml-review.md                   # 机器学习复习
│   ├── ml-exam-outline.md             # 机器学习考试大纲
│   ├── dl_basics.md                   # 深度学习基础（CNN/RNN/Transformer/训练技巧）
│   ├── nlp-intro.md                   # NLP 入门
│   ├── nlp-overview.md                # NLP 概述（发展历程/任务体系）
│   ├── nlp-review.md                  # NLP 复习
│   ├── calculus-fundamentals.md       # 微积分基础
│   ├── linear-algebra.md              # 线性代数（含 ML 应用）
│   ├── probability-statistics.md      # 概率论与数理统计
│   ├── python-fundamentals.md         # Python 基础
│   ├── data-structures-fundamentals.md # 数据结构基础
│   ├── data-structures-algorithms.md  # 数据结构与算法
│   ├── digital-image-processing-cv.md # 数字图像处理与计算机视觉
│   └── deep-reinforcement-learning/   # 深度强化学习（李宏毅课程）
│       ├── overview.md                #   课程总览
│       ├── 01-qlearning.md            #   Q-Learning / DQN
│       ├── 02-actor-critic.md         #   Actor-Critic / A3C
│       ├── 03-ppo.md                  #   PPO 近端策略优化
│       ├── 04-reward-shaping.md       #   Reward Shaping
│       ├── 05-inverse-rl.md           #   逆向强化学习 IRL
│       ├── *.pdf                      #   原始讲义（不会被 RAG 索引）
│       └── README.md                  #   子目录索引
│
├── 🐍 python-libraries/
│   ├── numpy-basics.md                # NumPy 基础
│   ├── pandas-basics.md               # Pandas 基础
│   ├── matplotlib-basics.md           # Matplotlib 基础
│   └── scikit-learn-basics.md         # Scikit-learn 基础
│
└── ✏️ 习题/
    ├── README.md                      # 习题索引
    ├── exercises.json                 # 习题元数据
    ├── 📝 module1_preprocessing/       # 数据预处理习题 (q01-q14)
    ├── 📝 module2_training/            # 模型训练习题 (q15-q41)
    ├── 📝 module3_deployment/          # 模型部署习题 (q42-q49)
    └── 📝 选择题/                      # 选择题 (4 套)
```

---

## 知识覆盖矩阵

| 领域 | 主题 | 文档数 | 状态 |
|------|------|--------|------|
| **数学基础** | 微积分、线性代数、概率统计 | 3 | ✅ 完整 |
| **编程基础** | Python、数据结构 | 2 | ✅ 完整 |
| **机器学习** | 监督学习、无监督学习、集成学习 | 11 | ✅ 完整 |
| **深度学习** | CNN、RNN/LSTM、Transformer、GAN、RL | 8 | ✅ 完整 |
| **NLP** | 文本处理、词嵌入、LLM、RAG | 3 | ✅ 完整 |
| **计算机视觉** | 图像处理、经典架构 | 1 | ⚠️ 可扩展 |
| **强化学习** | Q-Learning、Actor-Critic、PPO、IRL | 6 | ✅ 完整 |
| **Python 工具库** | NumPy、Pandas、Matplotlib、Scikit-learn | 4 | ✅ 完整 |
| **ML 工程实践** | 预处理、特征工程、模型评估 | 3 | ✅ 完整 |
| **习题库** | 预处理(14)、训练(27)、部署(8)、选择(4) | 53 | ✅ 完整 |

---

## 文档质量说明

### ✅ 格式规范文档
- 使用 `##`/`###` 进行层次化分段（便于 RAG 分块）
- 数学公式使用 LaTeX（`$$` 或 `$`）
- 包含代码示例（Python/C 语法高亮）
- 有明确的应用场景和学习建议

### ⚠️ 需注意的文档
- `deep-reinforcement-learning/` 中的 PDF 文件不会被 RAG 索引，仅作人工参考
- `probability-statistics.md` 原为课堂笔记，已规范化整理
- `linear-algebra.md` 原为课堂笔记，已规范化整理

---

## 后续扩展计划

- [ ] 计算机视觉专题：目标检测（YOLO/Faster R-CNN）、图像分割（U-Net/Mask R-CNN）
- [ ] NLP 专题扩增：BERT 微调实战、Prompt Engineering、RAG 实现详解
- [ ] 工具库扩展：PyTorch 基础、HuggingFace Transformers、LangChain
- [ ] MLOps：模型部署（Flask/FastAPI/ONNX）、MLflow 实验管理
- [ ] 大模型专题：LLM 训练（LoRA/QLoRA）、推理优化、Agent 开发
- [ ] 更多习题：补充解答与详细解析

---

## RAG 索引命令

```bash
# 在项目根目录执行
python backend/rag/knowledge_loader.py
```

该命令会遍历 `data/knowledge/` 下所有 `.md` 和 `.json` 文件，分块后向量化存入 ChromaDB。
