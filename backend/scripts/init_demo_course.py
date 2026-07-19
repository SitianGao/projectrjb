"""
演示课程初始化脚本 —— 为软件杯演示准备"人工智能与深度学习"课程闭环。

幂等：重复执行不会创建重复数据。

用法:
    python scripts/init_demo_course.py          # 直接运行
    python -c "from scripts.init_demo_course import init_demo_course; init_demo_course()"
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import sys
import uuid

# 确保 backend 在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from database import SessionLocal
from models.auth import Course, User
from models.student import Student
from models.learning_path import LearningPath, LearningTask
from models.evaluation import EvaluationReport, LearningRecord, WrongQuestion
from models.resource import Resource
from core.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)

# ── 演示配置常量 ──

DEMO_USER_ID = "demo_student"
DEMO_USERNAME = "demo_student"
DEMO_PASSWORD = "demo123"
DEMO_STUDENT_ID = "demo-student-ai-dl"
COURSE_ID = "ai_deep_learning_demo"
COURSE_TITLE = "人工智能与深度学习"
COURSE_GOAL = "掌握深度学习基础并完成简单图像分类项目"
KNOWLEDGE_BASE_ID = "kb_ai_deep_learning"
VECTOR_COLLECTION = "ai_deep_learning_documents"

# ── 四个演示阶段 ──

DEMO_STAGES = [
    {
        "stage_id": "stage_ai_basics",
        "title": "人工智能与机器学习基础",
        "order": 1,
        "description": "建立对人工智能和机器学习的基本认识，理解核心概念与工作流程",
        "status": "completed",
        "learning_objectives": [
            "能解释人工智能、机器学习、深度学习的关系与区别",
            "能区分监督学习和无监督学习的适用场景",
            "能描述训练集、验证集、测试集的划分原则",
            "能画出机器学习项目的完整流程图",
        ],
        "knowledge_point_ids": ["kp_ai_concept", "kp_supervised_learning", "kp_data_split", "kp_ml_pipeline"],
        "topics": ["人工智能基本概念", "监督学习与无监督学习", "训练集验证集测试集", "机器学习基本流程"],
        "estimated_days": 3,
        "tasks": [
            {
                "task_id": "task_ai_basics_goal",
                "task_type": "goal",
                "title": "阶段一学习目标",
                "description": "阅读本阶段学习目标，了解四个核心知识点的学习要求",
                "estimated_minutes": 10,
                "difficulty": "初级",
                "status": "completed",
                "prerequisite_task_ids": [],
            },
            {
                "task_id": "task_ai_basics_document",
                "task_type": "document",
                "title": "人工智能与机器学习基础核心讲义",
                "description": "阅读核心讲义，理解 AI/ML/DL 的关系、监督与无监督学习、数据划分和 ML 流程",
                "estimated_minutes": 30,
                "difficulty": "初级",
                "status": "completed",
                "prerequisite_task_ids": [],
            },
            {
                "task_id": "task_ai_basics_mindmap",
                "task_type": "mindmap",
                "title": "AI与ML基础概念知识导图",
                "description": "用思维导图梳理 AI 各分支的关系、学习范式分类和 ML 流程",
                "estimated_minutes": 15,
                "difficulty": "初级",
                "status": "completed",
                "prerequisite_task_ids": ["task_ai_basics_document"],
            },
            {
                "task_id": "task_ai_basics_exercise",
                "task_type": "exercise",
                "title": "AI基础概念专项练习",
                "description": "完成 3-5 道概念检查题，验证对 AI 基本概念和数据划分的理解",
                "estimated_minutes": 20,
                "difficulty": "初级",
                "status": "completed",
                "prerequisite_task_ids": ["task_ai_basics_document"],
            },
            {
                "task_id": "task_ai_basics_assessment",
                "task_type": "assessment",
                "title": "阶段一测评",
                "description": "完成阶段测评，验证是否掌握人工智能与机器学习基础",
                "estimated_minutes": 30,
                "difficulty": "初级",
                "status": "completed",
                "prerequisite_task_ids": ["task_ai_basics_exercise"],
            },
            {
                "task_id": "task_ai_basics_classroom",
                "task_type": "interactive_classroom",
                "title": "AI基础概念互动课堂",
                "description": "进入沉浸式互动课堂，通过AI教师讲解、白板演示和即时测验理解AI核心概念",
                "estimated_minutes": 25,
                "difficulty": "初级",
                "status": "not_started",
                "prerequisite_task_ids": ["task_ai_basics_assessment"],
            },
        ],
    },
    {
        "stage_id": "stage_gradient_descent",
        "title": "梯度下降与模型训练",
        "order": 2,
        "description": "深入理解梯度下降优化算法和模型训练的核心机制",
        "status": "active",
        "learning_objectives": [
            "能解释损失函数的作用和常见形式（MSE、交叉熵）",
            "能推导梯度下降的参数更新公式",
            "能分析学习率对训练收敛的影响",
            "能识别过拟合和欠拟合现象并提出解决方案",
        ],
        "knowledge_point_ids": ["kp_loss_function", "kp_gradient", "kp_gradient_descent", "kp_learning_rate", "kp_overfitting"],
        "topics": ["损失函数", "梯度", "梯度下降", "学习率", "过拟合与欠拟合"],
        "estimated_days": 4,
        "tasks": [
            {
                "task_id": "task_gd_goal",
                "task_type": "goal",
                "title": "阶段二学习目标",
                "description": "阅读本阶段学习目标，了解梯度下降相关知识点",
                "estimated_minutes": 10,
                "difficulty": "初级",
                "status": "completed",
                "prerequisite_task_ids": [],
            },
            {
                "task_id": "task_gd_document",
                "task_type": "document",
                "title": "梯度下降核心讲义",
                "description": "阅读梯度下降核心讲义，理解损失函数、梯度、学习率和过拟合",
                "estimated_minutes": 30,
                "difficulty": "中级",
                "status": "active",
                "prerequisite_task_ids": [],
            },
            {
                "task_id": "task_gd_mindmap",
                "task_type": "mindmap",
                "title": "梯度下降知识导图",
                "description": "用思维导图梳理损失函数→梯度→参数更新的完整链路",
                "estimated_minutes": 15,
                "difficulty": "中级",
                "status": "pending",
                "prerequisite_task_ids": ["task_gd_document"],
            },
            {
                "task_id": "task_gd_exercise",
                "task_type": "exercise",
                "title": "学习率专项练习",
                "description": "完成 3-5 道关于学习率选择和模型收敛的练习题",
                "estimated_minutes": 20,
                "difficulty": "中级",
                "status": "pending",
                "prerequisite_task_ids": ["task_gd_document"],
            },
            {
                "task_id": "task_gd_assessment",
                "task_type": "assessment",
                "title": "阶段二测评",
                "description": "完成阶段测评，验证是否掌握梯度下降与模型训练",
                "estimated_minutes": 30,
                "difficulty": "中级",
                "status": "locked",
                "prerequisite_task_ids": ["task_gd_exercise", "task_gd_mindmap"],
            },
            {
                "task_id": "task_gradient_classroom",
                "task_type": "interactive_classroom",
                "title": "梯度下降与学习率互动课堂",
                "description": "进入沉浸式互动课堂，通过交互模拟、代码案例和AI讨论理解梯度下降原理",
                "estimated_minutes": 25,
                "difficulty": "中级",
                "status": "not_started",
                "prerequisite_task_ids": ["task_gd_assessment"],
            },
        ],
    },
    {
        "stage_id": "stage_neural_network",
        "title": "神经网络与反向传播",
        "order": 3,
        "description": "掌握神经元模型、激活函数、前向传播和反向传播算法",
        "status": "locked",
        "learning_objectives": [
            "能画出单个神经元的结构并说明各组件作用",
            "能对比常见激活函数（Sigmoid、ReLU、Tanh）的优缺点",
            "能手算一个简单网络的前向传播过程",
            "能解释反向传播的链式求导原理",
        ],
        "knowledge_point_ids": ["kp_neuron", "kp_activation", "kp_forward_prop", "kp_backprop", "kp_param_update"],
        "topics": ["神经元模型", "激活函数", "前向传播", "反向传播", "参数更新"],
        "estimated_days": 4,
        "unlock_conditions": ["stage_gradient_descent 测评通过"],
        "tasks": [
            {
                "task_id": "task_nn_goal",
                "task_type": "goal",
                "title": "阶段三学习目标",
                "description": "阅读本阶段学习目标，了解神经网络核心知识点",
                "estimated_minutes": 10,
                "difficulty": "初级",
                "status": "pending",
                "prerequisite_task_ids": [],
            },
            {
                "task_id": "task_nn_document",
                "task_type": "document",
                "title": "神经网络与反向传播核心讲义",
                "description": "阅读核心讲义，理解神经元、激活函数、前向/反向传播",
                "estimated_minutes": 35,
                "difficulty": "中级",
                "status": "pending",
                "prerequisite_task_ids": [],
            },
            {
                "task_id": "task_nn_mindmap",
                "task_type": "mindmap",
                "title": "神经网络结构知识导图",
                "description": "用思维导图梳理网络层级结构、激活函数选择和数据流动",
                "estimated_minutes": 15,
                "difficulty": "中级",
                "status": "pending",
                "prerequisite_task_ids": ["task_nn_document"],
            },
            {
                "task_id": "task_nn_exercise",
                "task_type": "exercise",
                "title": "反向传播专项练习",
                "description": "完成关于链式求导和反向传播计算的练习",
                "estimated_minutes": 25,
                "difficulty": "中高级",
                "status": "pending",
                "prerequisite_task_ids": ["task_nn_document"],
            },
            {
                "task_id": "task_nn_assessment",
                "task_type": "assessment",
                "title": "阶段三测评",
                "description": "完成阶段测评，验证是否掌握神经网络与反向传播",
                "estimated_minutes": 30,
                "difficulty": "中高级",
                "status": "locked",
                "prerequisite_task_ids": ["task_nn_exercise", "task_nn_mindmap"],
            },
            {
                "task_id": "task_neural_network_classroom",
                "task_type": "interactive_classroom",
                "title": "神经网络互动课堂",
                "description": "进入沉浸式互动课堂，学习神经元模型、激活函数和反向传播算法",
                "estimated_minutes": 25,
                "difficulty": "中高级",
                "status": "not_started",
                "prerequisite_task_ids": ["task_nn_assessment"],
            },
        ],
    },
    {
        "stage_id": "stage_cnn",
        "title": "卷积神经网络与图像分类",
        "order": 4,
        "description": "掌握卷积运算、CNN 架构和图像分类实践",
        "status": "locked",
        "learning_objectives": [
            "能解释卷积运算的数学原理和物理意义",
            "能画出典型 CNN 架构（Conv→Pool→FC）",
            "能说明池化层的作用和常见类型",
            "能完成一个简单的图像分类项目并评估模型性能",
        ],
        "knowledge_point_ids": ["kp_convolution", "kp_conv_layer", "kp_pooling", "kp_feature_extraction", "kp_image_classification", "kp_model_eval"],
        "topics": ["卷积运算", "卷积层", "池化层", "特征提取", "图像分类", "模型评估"],
        "estimated_days": 5,
        "unlock_conditions": ["stage_neural_network 测评通过"],
        "tasks": [
            {
                "task_id": "task_cnn_goal",
                "task_type": "goal",
                "title": "阶段四学习目标",
                "description": "阅读本阶段学习目标，了解 CNN 核心知识点",
                "estimated_minutes": 10,
                "difficulty": "初级",
                "status": "pending",
                "prerequisite_task_ids": [],
            },
            {
                "task_id": "task_cnn_document",
                "task_type": "document",
                "title": "卷积神经网络核心讲义",
                "description": "阅读核心讲义，理解卷积、池化、特征提取和图像分类",
                "estimated_minutes": 35,
                "difficulty": "中高级",
                "status": "pending",
                "prerequisite_task_ids": [],
            },
            {
                "task_id": "task_cnn_mindmap",
                "task_type": "mindmap",
                "title": "CNN架构知识导图",
                "description": "用思维导图梳理 Conv→Pool→FC 完整架构",
                "estimated_minutes": 15,
                "difficulty": "中高级",
                "status": "pending",
                "prerequisite_task_ids": ["task_cnn_document"],
            },
            {
                "task_id": "task_cnn_exercise",
                "task_type": "exercise",
                "title": "CNN图像分类专项练习",
                "description": "完成关于卷积运算和图像分类的练习",
                "estimated_minutes": 25,
                "difficulty": "中高级",
                "status": "pending",
                "prerequisite_task_ids": ["task_cnn_document"],
            },
            {
                "task_id": "task_cnn_assessment",
                "task_type": "assessment",
                "title": "阶段四测评",
                "description": "完成最终测评，验证是否掌握卷积神经网络与图像分类",
                "estimated_minutes": 35,
                "difficulty": "高级",
                "status": "locked",
                "prerequisite_task_ids": ["task_cnn_exercise", "task_cnn_mindmap"],
            },
            {
                "task_id": "task_cnn_classroom",
                "task_type": "interactive_classroom",
                "title": "CNN图像分类互动课堂",
                "description": "进入沉浸式互动课堂，通过卷积可视化和代码案例理解图像分类原理",
                "estimated_minutes": 25,
                "difficulty": "高级",
                "status": "not_started",
                "prerequisite_task_ids": ["task_cnn_assessment"],
            },
        ],
    },
]

# ── 预置演示资源（agent_pre_generated：模拟 Agent 全链路生成结果）──

DEMO_RESOURCES = [
    # ==================== Stage 1: AI/ML 基础 ====================
    {
        "resource_type": "document",
        "title": "人工智能与机器学习基础核心讲义",
        "topic": "人工智能与机器学习基础",
        "difficulty": "初级",
        "stage_id": "stage_ai_basics",
        "task_id": "task_ai_basics_document",
        "summary": "全面讲解AI/ML/DL的关系、监督与无监督学习、数据划分、ML项目流程",
        "estimated_minutes": 30,
        "content": {
            "learning_objectives": [
                "能解释人工智能、机器学习、深度学习的关系与区别",
                "能区分监督学习和无监督学习的适用场景",
                "能描述训练集、验证集、测试集的划分原则",
                "能画出机器学习项目的完整流程图",
            ],
            "sections": [
                {
                    "heading": "1. 什么是人工智能？",
                    "paragraphs": [
                        "人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，目标是让机器能够模拟人类的智能行为，包括感知、推理、学习和决策。",
                        "AI 可以追溯到 1956 年达特茅斯会议。经过几十年的发展，AI 已经渗透到我们生活的方方面面：手机上的语音助手、购物网站的推荐系统、自动驾驶汽车、医疗影像诊断等。",
                        "AI 的终极目标是通用人工智能（AGI）——让机器具备和人类一样广泛的智能。目前我们距离 AGI 还有很长的路要走，但在特定领域（如围棋、蛋白质折叠），AI 已经超越了人类。",
                    ],
                    "examples": [
                        "AlphaGo 击败围棋世界冠军——这是 AI 在特定任务上超越人类的里程碑",
                        "ChatGPT 能够理解和生成自然语言——这是大语言模型（LLM）的应用",
                        "手机人脸解锁——计算机视觉技术的日常应用",
                    ],
                    "key_points": [
                        "AI 的目标是让机器模拟人类智能",
                        "AI ≠ 人类智能，目前属于「弱人工智能」阶段",
                    ],
                },
                {
                    "heading": "2. 人工智能 → 机器学习 → 深度学习",
                    "paragraphs": [
                        "这三者的关系是层层包含的：AI 是最大的概念，机器学习（ML）是实现 AI 的一种方法，深度学习（DL）是机器学习的一个子领域。",
                        "传统 AI 依赖人工编写规则（如专家系统），但现实世界太复杂，规则难以穷举。机器学习改变了这一范式：不给机器写规则，而是让机器从数据中自己学出规律。",
                        "深度学习使用多层神经网络，能够自动从原始数据（图像像素、文本字符）中提取特征，避免了传统 ML 中繁琐的人工特征工程。2012 年 AlexNet 在 ImageNet 上的突破标志着深度学习时代的到来。",
                    ],
                    "examples": [
                        "传统编程：输入 + 规则 → 输出（如：邮件含'中奖'→ 标记为垃圾邮件）",
                        "机器学习：输入 + 输出 → 规则（如：给 10 万封标注好的邮件，让模型学出什么是垃圾邮件）",
                    ],
                    "key_points": [
                        "AI ⊃ ML ⊃ DL，是层层包含的关系",
                        "机器学习的核心是让机器从数据中学习，而非人工编写规则",
                        "深度学习擅长自动特征提取，在图像、语音、文本领域效果显著",
                    ],
                },
                {
                    "heading": "3. 监督学习 vs 无监督学习",
                    "paragraphs": [
                        "监督学习（Supervised Learning）是机器学习中最常见的形式。训练数据包含输入和对应的正确答案（标签），模型学习「输入 → 输出」的映射关系。",
                        "无监督学习（Unsupervised Learning）的训练数据只有输入，没有标签。模型需要自己发现数据中的结构、模式或分组。",
                        "除了这两种，还有半监督学习（部分数据有标签）和强化学习（通过奖励信号学习），它们在特定场景下各有优势。",
                    ],
                    "examples": [
                        "监督学习：用标注了「猫」或「狗」的照片训练分类器；用历史房价数据预测未来房价",
                        "无监督学习：把电商用户按购买行为自动分组（聚类）；把 1000 篇文章按主题归类",
                        "强化学习：AlphaGo 通过自我对弈不断提升棋力；机器人通过试错学习走路",
                    ],
                    "key_points": [
                        "监督学习需要标签数据，目标是学习「输入→输出」的映射",
                        "无监督学习不需要标签，目标是发现数据内在结构",
                        "选择哪种学习方式取决于你有什么样的数据",
                    ],
                },
                {
                    "heading": "4. 训练集、验证集、测试集",
                    "paragraphs": [
                        "在机器学习项目中，数据需要划分为三个互不重叠的子集。训练集（Training Set）用于训练模型参数；验证集（Validation Set）用于调整超参数和选择模型；测试集（Test Set）用于最终评估模型的泛化能力。",
                        "常见的划分比例是 70% 训练 / 15% 验证 / 15% 测试，或 80% / 10% / 10%。数据量越大，验证集和测试集的比例可以越小。",
                        "为什么要严格分开？因为模型的最终目标是「泛化」——在没见过的新数据上表现好。如果在测试集上调参，就相当于「考试前偷看了答案」，测试分数会很漂亮但实际使用时会翻车。",
                    ],
                    "examples": [
                        "假设有 10000 条标注数据：7000 条训练，1500 条验证，1500 条测试",
                        "训练集上准确率 99%，测试集上准确率 75% → 过拟合，模型死记硬背了训练数据",
                        "训练集和测试集上准确率都只有 60% → 欠拟合，模型太简单学不到规律",
                    ],
                    "key_points": [
                        "三个集合必须互不重叠",
                        "训练集→学参数，验证集→调超参，测试集→最终评估",
                        "测试集只能在最后用一次，不能反复用来调模型",
                    ],
                },
                {
                    "heading": "5. 机器学习项目的完整流程",
                    "paragraphs": [
                        "一个典型的 ML 项目包含以下阶段：① 问题定义（要解决什么问题？业务指标是什么？）；② 数据收集与清洗（获取原始数据，处理缺失值、异常值）；③ 探索性数据分析（可视化、统计摘要，理解数据分布）；④ 特征工程（选择、构造、变换特征）；⑤ 模型选择与训练（尝试多个模型，交叉验证选最优）；⑥ 模型评估与调优（在验证集上评估，调超参数）；⑦ 部署与监控（将模型上线，持续监控性能衰减）。",
                    ],
                    "examples": [
                        "房产估价项目：定义目标（预测房价）→ 收集历史成交数据 → 清洗（处理缺失的房龄）→ 特征（构造'每平米单价'）→ 训练线性回归/XGBoost → 评估 MAE → 部署 API",
                    ],
                    "key_points": [
                        "ML 项目是端到端的系统工程，模型训练只占一小部分",
                        "数据和特征的质量决定了模型性能的上限",
                        "部署后才真正产生业务价值，但需要持续监控",
                    ],
                },
            ],
            "summary": "人工智能是一个广阔领域，机器学习是当前实现 AI 的主要方法，深度学习则进一步推动了 AI 的爆发。理解监督/无监督学习的区别、数据划分原则和项目流程，是后续学习所有算法和模型的基础。",
            "common_mistakes": [
                "认为 AI = 深度学习：AI 包括很多其他方法（知识图谱、进化算法等）",
                "混淆验证集和测试集：验证集可以多次使用，测试集只能用一次",
                "在测试集上调参后报告结果：这是数据泄露，会导致过高的虚假性能估计",
                "认为无监督学习「没用」：现实中大部分数据没有标签，无监督学习非常实用",
            ],
        },
    },
    {
        "resource_type": "mindmap",
        "title": "AI与ML基础概念知识导图",
        "topic": "人工智能与机器学习基础",
        "difficulty": "初级",
        "stage_id": "stage_ai_basics",
        "task_id": "task_ai_basics_mindmap",
        "summary": "AI 各分支关系、学习范式分类和 ML 项目流程的层级可视化",
        "estimated_minutes": 15,
        "content": {
            "root": {
                "id": "root",
                "label": "人工智能（AI）",
                "description": "让机器模拟人类智能的科学",
                "children": [
                    {
                        "id": "ml",
                        "label": "机器学习（ML）",
                        "description": "从数据中学习规律",
                        "children": [
                            {"id": "supervised", "label": "监督学习", "description": "有标签数据训练", "children": [
                                {"id": "classify", "label": "分类", "description": "预测离散类别（是/否）", "children": []},
                                {"id": "regression", "label": "回归", "description": "预测连续数值", "children": []},
                            ]},
                            {"id": "unsupervised", "label": "无监督学习", "description": "无标签数据训练", "children": [
                                {"id": "cluster", "label": "聚类", "description": "自动分组", "children": []},
                                {"id": "dim_reduce", "label": "降维", "description": "压缩特征空间", "children": []},
                            ]},
                            {"id": "rl", "label": "强化学习", "description": "通过奖励信号学习", "children": []},
                        ],
                    },
                    {
                        "id": "dl",
                        "label": "深度学习（DL）",
                        "description": "多层神经网络",
                        "children": [
                            {"id": "cnn_node", "label": "CNN", "description": "卷积神经网络→图像", "children": []},
                            {"id": "rnn_node", "label": "RNN/Transformer", "description": "序列模型→文本", "children": []},
                            {"id": "gan_node", "label": "GAN", "description": "生成对抗网络→生成", "children": []},
                        ],
                    },
                    {
                        "id": "pipeline",
                        "label": "ML项目流程",
                        "description": "从问题到部署",
                        "children": [
                            {"id": "step1", "label": "①问题定义", "description": "明确目标与指标", "children": []},
                            {"id": "step2", "label": "②数据准备", "description": "收集、清洗、标注", "children": []},
                            {"id": "step3", "label": "③特征工程", "description": "选择与构造特征", "children": []},
                            {"id": "step4", "label": "④模型训练", "description": "选择算法、调参", "children": []},
                            {"id": "step5", "label": "⑤评估部署", "description": "测试、上线、监控", "children": []},
                        ],
                    },
                    {
                        "id": "data_split",
                        "label": "数据划分",
                        "description": "训练集/验证集/测试集",
                        "children": [
                            {"id": "train", "label": "训练集 70%", "description": "训练模型参数", "children": []},
                            {"id": "val", "label": "验证集 15%", "description": "调超参数", "children": []},
                            {"id": "test", "label": "测试集 15%", "description": "最终评估", "children": []},
                        ],
                    },
                ],
            }
        },
    },
    {
        "resource_type": "exercise",
        "title": "AI基础概念专项练习",
        "topic": "人工智能与机器学习基础",
        "difficulty": "初级",
        "stage_id": "stage_ai_basics",
        "task_id": "task_ai_basics_exercise",
        "summary": "5 道选择题检验对 AI 基本概念、学习范式和数据划分的理解",
        "estimated_minutes": 20,
        "content": {
            "instructions": "请完成以下 5 道单选题，检验你对 AI 基础概念的理解。每题选择最佳答案。",
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "stem": "关于人工智能（AI）、机器学习（ML）和深度学习（DL）的关系，以下说法正确的是？",
                    "options": [
                        {"key": "A", "text": "AI 是 DL 的子集，DL 是 ML 的子集"},
                        {"key": "B", "text": "DL 是 ML 的子集，ML 是 AI 的子集"},
                        {"key": "C", "text": "三者是完全独立的技术"},
                        {"key": "D", "text": "ML 和 DL 是同一概念的不同名称"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "AI 是最广的概念。机器学习是实现 AI 的方法之一，深度学习是机器学习中基于多层神经网络的一个子领域。即 AI ⊃ ML ⊃ DL。",
                    "difficulty": "easy",
                    "knowledge_point_ids": ["kp_ai_concept"],
                },
                {
                    "id": "q2",
                    "type": "single_choice",
                    "stem": "手写数字识别任务中，给模型 60000 张标注了「0-9」的手写数字图片进行训练，这属于哪种学习方式？",
                    "options": [
                        {"key": "A", "text": "无监督学习"},
                        {"key": "B", "text": "监督学习"},
                        {"key": "C", "text": "强化学习"},
                        {"key": "D", "text": "自监督学习"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "每张图片都有对应的数字标签（0-9），即训练数据包含输入（图片）和正确答案（标签），这是典型的监督学习任务。",
                    "difficulty": "easy",
                    "knowledge_point_ids": ["kp_supervised_learning"],
                },
                {
                    "id": "q3",
                    "type": "single_choice",
                    "stem": "一个电商网站想根据用户的购买历史，自动将用户分成几个不同的群体以便精准营销。这适合用什么方法？",
                    "options": [
                        {"key": "A", "text": "回归分析"},
                        {"key": "B", "text": "分类"},
                        {"key": "C", "text": "聚类"},
                        {"key": "D", "text": "目标检测"},
                    ],
                    "correct_answer": ["C"],
                    "explanation": "用户没有被预先标注属于哪个群体，需要算法自动发现数据中的分组结构。聚类是无监督学习的典型任务，适合客户分群、主题发现等场景。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_supervised_learning"],
                },
                {
                    "id": "q4",
                    "type": "single_choice",
                    "stem": "在 ML 项目中，验证集（Validation Set）的主要用途是什么？",
                    "options": [
                        {"key": "A", "text": "训练模型的可学习参数（如权重）"},
                        {"key": "B", "text": "调整超参数和选择最优模型"},
                        {"key": "C", "text": "最终评估模型的泛化能力"},
                        {"key": "D", "text": "存储测试数据的副本"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "训练集用于学习模型参数（如线性回归的系数）。验证集用于调节超参数（如学习率、网络层数）并选择表现最好的模型。测试集只在最后用一次，评估最终性能。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_data_split"],
                },
                {
                    "id": "q5",
                    "type": "single_choice",
                    "stem": "一个 ML 模型在训练集上准确率高达 98%，但在测试集上只有 65%。这最可能是什么问题？",
                    "options": [
                        {"key": "A", "text": "欠拟合"},
                        {"key": "B", "text": "过拟合"},
                        {"key": "C", "text": "数据标注错误"},
                        {"key": "D", "text": "学习率设置过大"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "训练集表现远好于测试集是过拟合的典型症状。模型「死记硬背」了训练数据的噪声和特例，而不是学到通用的规律，导致在没见过的新数据上性能大幅下降。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_ml_pipeline"],
                },
            ],
        },
    },

    # ==================== Stage 2: 梯度下降 ====================
    {
        "resource_type": "document",
        "title": "梯度下降核心讲义",
        "topic": "梯度下降与模型训练",
        "difficulty": "中级",
        "stage_id": "stage_gradient_descent",
        "task_id": "task_gd_document",
        "summary": "深入讲解损失函数、梯度计算、参数更新、学习率调优与过拟合识别",
        "estimated_minutes": 30,
        "content": {
            "learning_objectives": [
                "能解释损失函数的作用和常见形式（MSE、交叉熵）",
                "能推导梯度下降的参数更新公式",
                "能分析学习率对训练收敛的影响",
                "能识别过拟合和欠拟合现象并提出解决方案",
            ],
            "sections": [
                {
                    "heading": "1. 损失函数——衡量模型有多「错」",
                    "paragraphs": [
                        "损失函数（Loss Function）是机器学习中最核心的概念之一。它的作用是量化模型预测值与真实值之间的差距——差距越大，损失越大，模型越差。训练的目标就是让损失最小化。",
                        "回归任务最常用的是均方误差（MSE）：计算每个样本的预测误差的平方，再取平均。MSE 对大误差特别敏感（因为平方放大了误差），所以它会优先修正那些偏差最大的预测。",
                        "分类任务最常用的是交叉熵损失（Cross-Entropy Loss）。它衡量的不是距离，而是两个概率分布之间的差异。当模型对正确类别的预测概率接近 1 时，交叉熵接近 0；当模型对正确类别预测概率接近 0 时，交叉熵趋近无穷。",
                    ],
                    "examples": [
                        "房价预测（回归）：真实值 500 万，预测 450 万 → 误差 50 万 → MSE 贡献 2500",
                        "猫狗分类（分类）：真实标签「猫」，模型预测「猫:0.9 狗:0.1」→ 交叉熵很小，模型表现好",
                        "猫狗分类：真实标签「猫」，模型预测「猫:0.1 狗:0.9」→ 交叉熵很大，模型需要大幅调整",
                    ],
                    "key_points": [
                        "损失函数是优化目标——训练就是不断降低损失",
                        "回归用 MSE，分类用交叉熵，不同的任务需要不同的损失函数",
                        "损失值本身没有绝对意义，它的变化趋势才重要",
                    ],
                },
                {
                    "heading": "2. 梯度——函数增长最快的方向",
                    "paragraphs": [
                        "在微积分中，导数描述一元函数在某一点的变化率。梯度（Gradient）是导数在多元函数上的推广——它是一个向量，每个分量是函数对该变量的偏导数。",
                        "梯度有一个非常重要的几何性质：梯度向量指向函数值增长最快的方向，梯度的模（长度）等于最大增长率。换句话说，沿着梯度方向走，函数值增加得最快；沿着负梯度方向走，函数值减小得最快。",
                        "举个例子：站在山坡上（函数 f(x, y) = 高度），梯度指向「最陡的上坡方向」。如果你想到达山谷（最低点），就应该沿着负梯度方向——也就是最陡的下坡方向——走。这就是「梯度下降」名字的由来。",
                        "对于损失函数 J(θ)，梯度 ∇J(θ) 在参数空间中指出「损失上升最快的方向」。因为我们想让损失最小化，就沿着负梯度方向更新参数。",
                    ],
                    "examples": [
                        "一元函数 f(x) = x²：导数 f'(x) = 2x。在 x=3 处导数为 6（正），说明往 x 增大方向函数值增大；往 x 减小方向（负梯度）函数值减小",
                        "二元函数 f(x,y) = x² + y²：梯度 ∇f = (2x, 2y)。在点 (1,2) 处梯度为 (2,4)，指向远离原点方向——确实，原点是最低点，离原点越远函数值越大",
                    ],
                    "key_points": [
                        "梯度 ∇f 是一个向量，每个分量是偏导数",
                        "梯度指向函数增长最快的方向",
                        "负梯度指向函数下降最快的方向——这就是梯度下降",
                    ],
                },
                {
                    "heading": "3. 梯度下降算法——一步步走向最优",
                    "paragraphs": [
                        "梯度下降的核心思想非常简单：从某个初始参数值出发，每次沿负梯度方向迈一小步，不断迭代直到收敛。参数更新公式为：θ_{new} = θ_{old} - α × ∇J(θ_{old})",
                        "α 是学习率（Learning Rate），控制每步的步长。∇J(θ) 是当前位置的梯度，告诉我们该往哪个方向走。",
                        "根据每次计算梯度使用的数据量，梯度下降有三种变体：批量梯度下降（BGD）使用全部训练数据计算梯度，最精确但计算量大；随机梯度下降（SGD）每次只用 1 个样本，计算快但不稳定；小批量梯度下降（Mini-batch GD）是折中方案，每次用一小批（如 32/64 个）样本，兼顾速度和稳定性，是目前最常用的。",
                    ],
                    "examples": [
                        "用 MSE 损失拟合直线 y = wx + b：损失 J(w,b) = Σ(y_i - (wx_i + b))² / n，梯度 ∂J/∂w = -2 Σ x_i(y_i - wx_i - b) / n，每次迭代 w = w - α × ∂J/∂w",
                        "从 θ₀ = 0 出发，梯度 = 10，学习率 α = 0.01 → θ₁ = 0 - 0.01×10 = -0.1",
                        "学习率 α = 0.01，经过 1000 次迭代 → 参数收敛到接近最优值",
                    ],
                    "key_points": [
                        "参数更新公式：θ_new = θ_old - α∇J(θ_old)",
                        "BGD 精确但慢，SGD 快但不稳，Mini-batch 折中最常用",
                        "梯度下降不保证找到全局最优（对于非凸函数），但实践中效果很好",
                    ],
                },
                {
                    "heading": "4. 学习率——最重要的超参数",
                    "paragraphs": [
                        "学习率 α 可能是机器学习中最重要的超参数。它控制每次参数更新的步长，直接影响模型能否收敛以及收敛速度。",
                        "学习率过大 → 步长太大，可能在最优解附近来回震荡，甚至导致损失越来越大（发散）；学习率过小 → 收敛极其缓慢，可能需要几百万次迭代才能到达最优解附近；学习率适中 → 快速稳定地收敛到最优。",
                        "实践中常用的技巧是学习率衰减（Learning Rate Decay）：训练初期用较大学习率快速接近最优，随着训练进行逐渐减小学习率以精细调整。还有自适应学习率方法（如 Adam、RMSprop），能自动为每个参数调整不同的学习率。",
                    ],
                    "examples": [
                        "α = 0.1 → 步长太大，loss 震荡，可能不收敛",
                        "α = 0.01 → 合适的学习率，loss 稳定下降",
                        "α = 0.00001 → 步长太小，loss 下降极其缓慢，训练时间过长",
                        "学习率衰减策略：α_t = α₀ / (1 + decay_rate × t)，随训练 epoch 逐步减小",
                    ],
                    "key_points": [
                        "学习率太小：收敛慢；学习率太大：震荡/发散",
                        "常用初始值：0.01 或 0.001",
                        "学习率衰减和自适应方法（Adam）能有效改善训练",
                    ],
                },
                {
                    "heading": "5. 过拟合与欠拟合",
                    "paragraphs": [
                        "过拟合（Overfitting）是指模型在训练数据上表现极好，但在新数据上表现很差——模型「死记硬背」了训练集而非学到通用规律。欠拟合（Underfitting）则相反，模型在训练集上就表现不好，说明模型太简单，无法捕捉数据中的模式。",
                        "判断过拟合的关键信号：训练 loss 持续下降，但验证 loss 不降反升。这时训练集上的「好成绩」是在「作弊」——模型背下了训练数据的噪声。",
                        "应对过拟合的方法：① 增加训练数据（最有效）；② 正则化（L1/L2 正则、Dropout）；③ 早停（验证 loss 不再下降时停止训练）；④ 减小模型复杂度。应对欠拟合的方法：① 增加模型复杂度；② 添加更多特征；③ 减少正则化强度。",
                    ],
                    "examples": [
                        "过拟合案例：用 100 次多项式拟合 10 个点，曲线完美穿过所有点但在点之间剧烈波动",
                        "欠拟合案例：用直线拟合非线性分布的房价数据，无论怎么调参效果都不好",
                        "理想状态：训练 loss 和验证 loss 都很低且接近——模型学到了真正的规律",
                    ],
                    "key_points": [
                        "过拟合：训练好测试差 → 模型背答案了",
                        "欠拟合：训练测试都差 → 模型太简单了",
                        "验证 loss 是最重要的监控指标，训练 loss 可能骗你",
                    ],
                },
            ],
            "summary": "梯度下降是深度学习的心脏。理解损失函数如何定义目标、梯度如何指引方向、学习率如何控制步长、以及如何识别过拟合，是训练任何模型的基础能力。这四个概念紧密相连，缺一不可。",
            "common_mistakes": [
                "混淆损失函数和评估指标：MSE 是训练用的损失，RMSE/R² 是评估用的指标",
                "认为梯度下降总能找到全局最优：对于非凸函数（如神经网络），梯度下降可能陷入局部最优",
                "只监控训练 loss：应该同时监控训练 loss 和验证 loss，验证 loss 才是判断泛化的关键",
                "学习率过大导致 loss 变成 NaN：这通常是梯度爆炸，需要降低学习率或使用梯度裁剪",
            ],
        },
    },
    {
        "resource_type": "mindmap",
        "title": "梯度下降知识导图",
        "topic": "梯度下降",
        "difficulty": "中级",
        "stage_id": "stage_gradient_descent",
        "task_id": "task_gd_mindmap",
        "summary": "梯度下降核心概念层级结构可视化",
        "estimated_minutes": 5,
        "content": {
            "root": {
                "id": "root",
                "label": "梯度下降优化",
                "description": "机器学习最核心的优化算法",
                "children": [
                    {
                        "id": "loss",
                        "label": "损失函数",
                        "description": "衡量预测与真实的差距",
                        "children": [
                            {"id": "mse", "label": "均方误差(MSE)", "description": "回归任务常用", "children": []},
                            {"id": "ce", "label": "交叉熵(CE)", "description": "分类任务常用", "children": []},
                        ],
                    },
                    {
                        "id": "gradient",
                        "label": "梯度计算",
                        "description": "损失对参数的偏导",
                        "children": [
                            {"id": "batch_gd", "label": "批量梯度下降", "description": "使用全部数据", "children": []},
                            {"id": "sgd", "label": "随机梯度下降", "description": "每次一个样本", "children": []},
                            {"id": "mini_batch", "label": "小批量梯度下降", "description": "折中方案", "children": []},
                        ],
                    },
                    {
                        "id": "lr",
                        "label": "学习率策略",
                        "description": "控制更新步长",
                        "children": [
                            {"id": "fixed_lr", "label": "固定学习率", "description": "最简单", "children": []},
                            {"id": "decay", "label": "学习率衰减", "description": "逐步减小", "children": []},
                            {"id": "adaptive", "label": "自适应学习率", "description": "Adam等", "children": []},
                        ],
                    },
                    {
                        "id": "overfit",
                        "label": "过拟合与欠拟合",
                        "description": "模型泛化问题",
                        "children": [
                            {"id": "over", "label": "过拟合", "description": "训练好测试差", "children": []},
                            {"id": "under", "label": "欠拟合", "description": "训练测试都差", "children": []},
                            {"id": "reg", "label": "正则化", "description": "防止过拟合", "children": []},
                        ],
                    },
                ],
            }
        },
    },
    {
        "resource_type": "exercise",
        "title": "学习率专项练习",
        "topic": "学习率",
        "difficulty": "中级",
        "stage_id": "stage_gradient_descent",
        "task_id": "task_gd_exercise",
        "summary": "验证对学习率选择和模型收敛的理解",
        "estimated_minutes": 20,
        "content": {
            "instructions": "请完成以下关于学习率的练习题，每题选择最佳答案。",
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "stem": "学习率过大可能导致什么后果？",
                    "options": [
                        {"key": "A", "text": "模型收敛过快，可能导致错过最优解"},
                        {"key": "B", "text": "损失函数值震荡或不收敛"},
                        {"key": "C", "text": "梯度计算错误"},
                        {"key": "D", "text": "以上都不对"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "学习率过大时，参数更新步长过大，会在最优解附近来回震荡，甚至导致损失值越来越大（发散）。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_learning_rate"],
                },
                {
                    "id": "q2",
                    "type": "single_choice",
                    "stem": "关于学习率衰减，以下说法正确的是？",
                    "options": [
                        {"key": "A", "text": "学习率必须始终保持不变"},
                        {"key": "B", "text": "训练初期用较大学习率快速收敛，后期用较小学习率精细调整"},
                        {"key": "C", "text": "学习率衰减只适用于深度学习，不适用于传统机器学习"},
                        {"key": "D", "text": "学习率衰减对模型性能没有影响"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "学习率衰减策略在训练初期用较大学习率加速收敛，后期减小学习率以便在最优解附近精细搜索，这是广泛使用的训练技巧。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_learning_rate"],
                },
                {
                    "id": "q3",
                    "type": "single_choice",
                    "stem": "当训练损失持续下降但验证损失开始上升时，最可能的原因是什么？",
                    "options": [
                        {"key": "A", "text": "学习率太小"},
                        {"key": "B", "text": "模型过拟合"},
                        {"key": "C", "text": "数据集太小"},
                        {"key": "D", "text": "梯度消失"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "训练损失下降但验证损失上升是过拟合的典型信号。模型在训练集上表现越来越好但泛化能力下降。可通过正则化、早停、数据增强等方法缓解。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_overfitting", "kp_learning_rate"],
                },
            ],
        },
    },
    {
        "resource_type": "ppt",
        "title": "神经网络结构课件",
        "topic": "神经网络",
        "difficulty": "中级",
        "stage_id": "stage_neural_network",
        "task_id": "task_nn_document",
        "summary": "神经网络结构教学课件，包含 10 张幻灯片",
        "estimated_minutes": 2,
        "content": {
            "theme": "神经网络与反向传播",
            "slides": [
                {"slide_number": 1, "title": "神经网络与反向传播", "layout": "title", "speaker_notes": "本课件面向中级学习者", "elements": []},
                {"slide_number": 2, "title": "学习目标", "layout": "content", "speaker_notes": "明确告知学员本节能力目标", "elements": []},
                {"slide_number": 3, "title": "神经元模型", "layout": "content", "speaker_notes": "从生物神经元类比引入", "elements": []},
                {"slide_number": 4, "title": "激活函数对比", "layout": "two_column", "speaker_notes": "Sigmoid vs ReLU vs Tanh", "elements": []},
                {"slide_number": 5, "title": "前向传播", "layout": "content", "speaker_notes": "逐步演示计算过程", "elements": []},
                {"slide_number": 6, "title": "反向传播原理", "layout": "content", "speaker_notes": "链式法则直观解释", "elements": []},
                {"slide_number": 7, "title": "代码示例", "layout": "content", "speaker_notes": "用 NumPy 实现简单网络", "elements": []},
                {"slide_number": 8, "title": "常见误区", "layout": "content", "speaker_notes": "3个典型错误", "elements": []},
                {"slide_number": 9, "title": "小结", "layout": "summary", "speaker_notes": "3个核心takeaway", "elements": []},
                {"slide_number": 10, "title": "课后任务", "layout": "summary", "speaker_notes": "必做+选做", "elements": []},
            ],
        },
    },
    {
        "resource_type": "document",
        "title": "反向传播核心讲义",
        "topic": "反向传播",
        "difficulty": "中高级",
        "stage_id": "stage_neural_network",
        "task_id": "task_nn_document",
        "summary": "深入讲解反向传播的链式求导原理和计算图方法",
        "estimated_minutes": 35,
        "content": {
            "learning_objectives": ["理解链式法则在神经网络中的应用", "能手算简单网络的反向传播", "理解梯度在计算图中的流动"],
            "sections": [
                {
                    "heading": "1. 链式法则回顾",
                    "paragraphs": ["反向传播的本质是链式法则的高效应用。对于复合函数 f(g(x))，其导数为 f'(g(x)) · g'(x)。"],
                    "examples": ["dz/dx = dz/dy · dy/dx"],
                    "key_points": ["链式法则是反向传播的数学基础", "计算图使反向传播可视化"],
                },
                {
                    "heading": "2. 计算图与梯度流动",
                    "paragraphs": ["计算图的每个节点代表一个操作，边代表数据流动。正向传播沿边计算输出，反向传播沿边反向传播梯度。"],
                    "examples": ["加法门对上游梯度不做改变", "乘法门将上游梯度乘以另一输入"],
                    "key_points": ["梯度在反向传播中按链式法则流动", "不同操作对梯度有不同影响"],
                },
            ],
            "summary": "反向传播通过链式法则高效计算所有参数的梯度，是训练深度神经网络的核心算法。",
            "common_mistakes": ["忘记对激活函数求导", "混淆矩阵求导的维度", "忽略批处理中的平均"],
        },
    },
    # ==================== Stage 3: 神经网络 ====================
    {
        "resource_type": "mindmap",
        "title": "神经网络结构知识导图",
        "topic": "神经网络与反向传播",
        "difficulty": "中级",
        "stage_id": "stage_neural_network",
        "task_id": "task_nn_mindmap",
        "summary": "神经网络层级结构、激活函数对比和数据流动的完整可视化",
        "estimated_minutes": 15,
        "content": {
            "root": {
                "id": "root",
                "label": "神经网络",
                "description": "模拟生物神经元的计算模型",
                "children": [
                    {
                        "id": "neuron",
                        "label": "神经元模型",
                        "description": "神经网络的基本单元",
                        "children": [
                            {"id": "input", "label": "输入 x₁, x₂, ...", "description": "来自上一层或原始数据", "children": []},
                            {"id": "weights", "label": "权重 wᵢ", "description": "每个输入的重要性", "children": []},
                            {"id": "bias", "label": "偏置 b", "description": "平移激活函数", "children": []},
                            {"id": "activation", "label": "激活函数 σ", "description": "引入非线性", "children": []},
                            {"id": "output", "label": "输出 a = σ(Σwᵢxᵢ + b)", "description": "传给下一层", "children": []},
                        ],
                    },
                    {
                        "id": "activations",
                        "label": "激活函数对比",
                        "description": "非线性变换的关键",
                        "children": [
                            {"id": "sigmoid", "label": "Sigmoid", "description": "输出(0,1)，饱和区梯度趋零→深层难训练", "children": []},
                            {"id": "tanh", "label": "Tanh", "description": "输出(-1,1)，零中心优于 Sigmoid但仍有饱和", "children": []},
                            {"id": "relu", "label": "ReLU", "description": "max(0,x)，计算快不饱和，但负半区死亡", "children": []},
                        ],
                    },
                    {
                        "id": "layers",
                        "label": "网络层级",
                        "description": "从输入到输出的数据流",
                        "children": [
                            {"id": "input_layer", "label": "输入层", "description": "接收原始特征", "children": []},
                            {"id": "hidden", "label": "隐藏层", "description": "逐层提取抽象特征", "children": []},
                            {"id": "output_layer", "label": "输出层", "description": "产生最终预测", "children": []},
                        ],
                    },
                    {
                        "id": "forward",
                        "label": "前向传播",
                        "description": "输入→逐层计算→输出",
                        "children": [
                            {"id": "fw1", "label": "z = Wx + b", "description": "线性变换", "children": []},
                            {"id": "fw2", "label": "a = σ(z)", "description": "激活", "children": []},
                            {"id": "fw3", "label": "Loss(a, y)", "description": "计算损失", "children": []},
                        ],
                    },
                    {
                        "id": "backward",
                        "label": "反向传播",
                        "description": "损失→逐层回传→梯度",
                        "children": [
                            {"id": "bw1", "label": "∂L/∂a", "description": "损失对输出梯度", "children": []},
                            {"id": "bw2", "label": "链式法则", "description": "∂L/∂w = ∂L/∂a·∂a/∂z·∂z/∂w", "children": []},
                            {"id": "bw3", "label": "参数更新", "description": "w = w - α·∂L/∂w", "children": []},
                        ],
                    },
                ],
            }
        },
    },
    {
        "resource_type": "exercise",
        "title": "反向传播专项练习",
        "topic": "反向传播",
        "difficulty": "中高级",
        "stage_id": "stage_neural_network",
        "task_id": "task_nn_exercise",
        "summary": "5 道题检验对链式求导、激活函数和反向传播计算的理解",
        "estimated_minutes": 25,
        "content": {
            "instructions": "请完成以下 5 道关于神经网络和反向传播的练习。",
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "stem": "在深度神经网络中，ReLU 相比 Sigmoid 的主要优势是什么？",
                    "options": [
                        {"key": "A", "text": "ReLU 的输出总是在 (0,1) 之间，更方便做二分类"},
                        {"key": "B", "text": "ReLU 在正半区梯度始终为 1，避免了 Sigmoid 的梯度饱和问题"},
                        {"key": "C", "text": "ReLU 的计算量比 Sigmoid 大很多"},
                        {"key": "D", "text": "ReLU 有零中心输出，比 Sigmoid 收敛更快"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "Sigmoid 在 x 很大或很小时导数趋近于 0（梯度饱和），导致深层网络难以训练。ReLU 在 x>0 时导数恒为 1，有效缓解了梯度消失，且计算简单。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_activation"],
                },
                {
                    "id": "q2",
                    "type": "single_choice",
                    "stem": "对于 sigmoid 激活函数 σ(z) = 1/(1+e⁻ᶻ)，其导数可以表示为？",
                    "options": [
                        {"key": "A", "text": "σ'(z) = σ(z)"},
                        {"key": "B", "text": "σ'(z) = σ(z)(1 - σ(z))"},
                        {"key": "C", "text": "σ'(z) = 1 - σ(z)"},
                        {"key": "D", "text": "σ'(z) = σ(z)²"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "Sigmoid 函数的一个优良性质：其导数可以用自身表示：σ'(z) = σ(z)(1-σ(z))。这在反向传播中非常方便——只需知道前向传播的输出值就能算出导数。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_backprop"],
                },
                {
                    "id": "q3",
                    "type": "single_choice",
                    "stem": "反向传播（Backpropagation）的核心数学原理是什么？",
                    "options": [
                        {"key": "A", "text": "泰勒展开"},
                        {"key": "B", "text": "链式法则（Chain Rule）"},
                        {"key": "C", "text": "拉格朗日乘数法"},
                        {"key": "D", "text": "傅里叶变换"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "反向传播的本质就是链式法则的系统性应用：从输出层向输入层逐层计算损失函数对各参数的偏导数。通过计算图，每一层的梯度可以高效地从后一层传递过来。",
                    "difficulty": "easy",
                    "knowledge_point_ids": ["kp_backprop"],
                },
                {
                    "id": "q4",
                    "type": "single_choice",
                    "stem": "在一个两层网络中，隐藏层使用 ReLU，输出层使用 Sigmoid 做二分类。反向传播时 ReLU 层的梯度计算正确的是？",
                    "options": [
                        {"key": "A", "text": "上游梯度 × 1（如果前向输入 > 0），否则上游梯度 × 0"},
                        {"key": "B", "text": "上游梯度 × sigmoid 导数的形式"},
                        {"key": "C", "text": "上游梯度 × tanh 导数的形式"},
                        {"key": "D", "text": "不管上游梯度，直接置零"},
                    ],
                    "correct_answer": ["A"],
                    "explanation": "ReLU 的导数是分段函数：x>0 时导数为 1，x≤0 时导数为 0。所以在反向传播中，ReLU 层将上游梯度乘以一个二元掩码：前向时激活的神经元原样传回梯度，未激活的神经元梯度截断为 0。",
                    "difficulty": "hard",
                    "knowledge_point_ids": ["kp_activation", "kp_backprop"],
                },
                {
                    "id": "q5",
                    "type": "single_choice",
                    "stem": "关于批处理（mini-batch）中的反向传播，以下说法正确的是？",
                    "options": [
                        {"key": "A", "text": "每个样本独立计算梯度后取平均作为最终梯度"},
                        {"key": "B", "text": "将所有样本的梯度相加（不取平均）"},
                        {"key": "C", "text": "只对第一个样本计算梯度"},
                        {"key": "D", "text": "随机选一个样本的梯度代表整个批次"},
                    ],
                    "correct_answer": ["A"],
                    "explanation": "Mini-batch 训练中，对批次内每个样本独立进行前向和反向传播计算各自的梯度，然后取平均值作为参数更新梯度。平均操作使得梯度估计更稳定（比单样本 SGD 噪声小），且计算效率高（比全量 BGD 快）。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_backprop", "kp_param_update"],
                },
            ],
        },
    },

    # ==================== Stage 4: CNN ====================
    {
        "resource_type": "document",
        "title": "卷积神经网络核心讲义",
        "topic": "卷积神经网络与图像分类",
        "difficulty": "中高级",
        "stage_id": "stage_cnn",
        "task_id": "task_cnn_document",
        "summary": "全面讲解卷积运算、CNN 架构、池化、特征提取和图像分类实践",
        "estimated_minutes": 35,
        "content": {
            "learning_objectives": [
                "能解释卷积运算的数学原理和物理意义",
                "能画出典型 CNN 架构（Conv→Pool→FC）",
                "能说明池化层的作用和常见操作",
                "能完成一个简单的图像分类项目并评估模型性能",
            ],
            "sections": [
                {
                    "heading": "1. 为什么要用卷积？——从全连接到局部连接",
                    "paragraphs": [
                        "如果直接用全连接网络处理图像，会遇到严重的参数爆炸。以一张 224×224×3 的彩色图片为例，全连接到 1000 个神经元就需要 224×224×3×1000 ≈ 1.5 亿个参数。这样的网络不仅计算量巨大，还极易过拟合。",
                        "卷积神经网络（CNN）的灵感来自生物学：大脑视觉皮层中的神经元只对视野中一小块区域（感受野）做出反应。CNN 用「卷积核」（也叫滤波器）在输入图像上滑动，每次只处理一个小窗口，同一个卷积核的参数在整个图像上共享，大幅减少了参数量。",
                        "这意味着：全连接层每个连接都有独立的权重；卷积层一个 3×3 的卷积核只有 9 个参数，无论输入图像是 100×100 还是 1000×1000，参数量不变。这就是卷积的「参数共享」特性。",
                    ],
                    "examples": [
                        "全连接：输入 1000 维，输出 1000 维 → 1000×1000 = 100 万个参数",
                        "卷积：输入 32×32 图像，3×3 卷积核 → 仅 9 个参数（再加 1 个偏置）",
                        "参数共享意味着：学到边缘检测的卷积核在图像的左上角和右下角都能工作",
                    ],
                    "key_points": [
                        "卷积解决全连接层的参数爆炸问题",
                        "参数共享：同一个卷积核在整个图像上复用",
                        "局部连接：每个神经元只连接输入的一小块区域",
                    ],
                },
                {
                    "heading": "2. 卷积运算——用数学描述图像操作",
                    "paragraphs": [
                        "卷积运算的本质是「加权求和」：将卷积核（一个小矩阵，如 3×3）放在输入图像的某个位置上，逐元素相乘再求和，得到输出特征图上的一个像素值。然后将卷积核向右或向下滑动（步长控制滑动的距离），重复上述操作，直到覆盖整个图像。",
                        "每个卷积核可以看作一个「特征检测器」。比如，一个卷积核的权重可能是 [[-1,-1,-1],[0,0,0],[1,1,1]]，它检测水平边缘——图像中从上到下亮度变化剧烈的区域。不同的卷积核检测不同的特征：边缘、纹理、颜色变化等。",
                        "多通道卷积：彩色图像有 RGB 三个通道，卷积核也有相同的深度。对 3 通道输入，3×3 卷积核实际是 3×3×3=27 个参数，每个通道独立做 2D 卷积后求和。一个卷积层通常有多个卷积核（如 64 个），每个产生一张特征图，输出就是 64 通道。",
                    ],
                    "examples": [
                        "输入 5×5，卷积核 3×3，步长 1，无填充 → 输出 (5-3+1)×(5-3+1) = 3×3",
                        "输入 32×32×3（RGB），64 个 3×3 卷积核 → 输出 32×32×64（每个核产生一个 32×32 的特征图）",
                        "边缘检测核 [[-1,-1,-1],[0,0,0],[1,1,1]] 对水平边界响应强烈，对纯色区域响应为 0",
                    ],
                    "key_points": [
                        "卷积 = 逐元素乘法 + 求和，核在输入上滑动",
                        "每个卷积核是一个特征检测器，不同核检测不同模式",
                        "多通道卷积核深度 = 输入通道数，输出通道数 = 卷积核个数",
                    ],
                },
                {
                    "heading": "3. 池化层——降维与平移不变性",
                    "paragraphs": [
                        "池化（Pooling）层通常插在卷积层之后，作用是降低特征图的空间尺寸（宽高），从而减少后续层的计算量和参数量。同时，池化也提供了一定的平移不变性——即使目标在图像中稍微偏移，池化后的特征响应仍然相似。",
                        "最常见的两种池化：最大池化（Max Pooling）取窗口内的最大值，保留了最强特征响应；平均池化（Average Pooling）取窗口内的平均值，更平滑但可能丢失锐利特征。实践中最大池化更常用。",
                        "典型的池化参数：2×2 窗口，步长 2。这意味着输出尺寸是输入的一半。经过几层 Conv+Pool 后，空间尺寸从 224×224 降到 7×7，但通道数从 3 增到 512。",
                    ],
                    "examples": [
                        "Max Pooling 2×2：输入 [[1,3],[2,4]] → 输出 4（取最大值）",
                        "输入 224×224×64 → Max Pool 2×2 stride 2 → 输出 112×112×64",
                        "平移不变性：猫在图片中右移 1 像素 → 卷积特征图也右移 1 → 池化后最大值位置不变",
                    ],
                    "key_points": [
                        "池化降维 = 减少计算量 + 增加感受野",
                        "Max Pooling 最常用，保留最强特征",
                        "池化提供有限的平移不变性",
                    ],
                },
                {
                    "heading": "4. CNN 典型架构——从 LeNet 到 ResNet",
                    "paragraphs": [
                        "经典的 CNN 架构遵循「Conv → ReLU → Pool」的重复模式，最后接全连接层做分类：输入图像 → [Conv+ReLU+Pool] × N → Flatten → FC → Softmax → 输出类别概率。",
                        "LeNet-5（1998）是第一个成功商用的 CNN，用于手写数字识别，架构简洁（Conv-Pool-Conv-Pool-FC-FC）但奠定了 CNN 的基本框架。",
                        "VGG（2014）的贡献是使用多个 3×3 小卷积核堆叠代替大卷积核——两个 3×3 的感受野等于一个 5×5，但参数更少、非线性更深。ResNet（2015）引入了「残差连接」（跳过连接），解决了深层网络的退化问题，使训练 152 层甚至更深的网络成为可能。",
                    ],
                    "examples": [
                        "LeNet-5: 输入 32×32 → Conv(6@5×5) → Pool → Conv(16@5×5) → Pool → FC(120) → FC(84) → 10 类输出",
                        "VGG-16: 13 个卷积层 + 3 个全连接层，全部使用 3×3 卷积",
                        "ResNet-50: 50 层，每个残差块 = Conv→BN→ReLU→Conv→BN + 跳过连接 → ReLU",
                    ],
                    "key_points": [
                        "经典模式：Conv→ReLU→Pool 循环 + FC 分类头",
                        "小卷积核堆叠 > 大卷积核（参数少、非线性多）",
                        "ResNet 残差连接让深层网络训练成为可能",
                    ],
                },
                {
                    "heading": "5. 图像分类完整项目流程",
                    "paragraphs": [
                        "一个典型的图像分类项目包含：① 数据准备——收集并标注图片，划分训练集/测试集，使用数据增强（随机翻转、旋转、颜色扰动）扩充训练数据；② 模型选择——根据任务复杂度选择预训练模型（如 ResNet-18）或自建小型 CNN；③ 训练配置——选择优化器（Adam/SGD）、损失函数（交叉熵）、学习率策略；④ 训练与监控——每个 epoch 记录训练 loss 和验证准确率，观察过拟合信号；⑤ 评估与部署——在测试集上计算准确率/精确率/召回率/混淆矩阵，分析错误案例。",
                    ],
                    "examples": [
                        "猫狗分类项目：收集 2000 张猫狗图片 → 数据增强扩到 8000 张 → 用 ResNet-18 预训练权重微调 → 5 epoch 达到 95% 准确率",
                        "数据增强示例：随机水平翻转、随机旋转 ±15°、颜色亮度 ±10%",
                        "混淆矩阵：预测猫 | 预测狗\n实际猫：450  (TN?) | 50\n实际狗：30 | 470",
                    ],
                    "key_points": [
                        "数据增强是防止过拟合最有效的手段之一",
                        "迁移学习（用预训练权重）大幅降低训练数据需求",
                        "混淆矩阵和准确率是评估分类模型的基础指标",
                    ],
                },
            ],
            "summary": "CNN 通过卷积核的参数共享和局部连接，极大减少了模型参数，并且天然适合处理网格结构的数据（图像、视频）。理解卷积运算、池化降维和经典架构的发展脉络，是进入计算机视觉领域的必备基础。",
            "common_mistakes": [
                "混淆卷积核大小和输出通道数：3×3 是核的空间尺寸，64 是核的个数（输出通道数）",
                "忘记卷积后特征图尺寸会变化：输出尺寸 = (输入尺寸 - 核尺寸 + 2×填充) / 步长 + 1",
                "认为池化是可学习的：池化没有可训练参数，它只是固定的下采样操作",
                "在浅层用太多通道：浅层特征图空间大，通道太多会导致计算爆炸",
            ],
        },
    },
    {
        "resource_type": "mindmap",
        "title": "CNN架构知识导图",
        "topic": "卷积神经网络与图像分类",
        "difficulty": "中高级",
        "stage_id": "stage_cnn",
        "task_id": "task_cnn_mindmap",
        "summary": "Conv→Pool→FC 完整架构、经典模型演化与图像分类流程可视化",
        "estimated_minutes": 15,
        "content": {
            "root": {
                "id": "root",
                "label": "卷积神经网络（CNN）",
                "description": "专为网格结构数据设计的深度学习模型",
                "children": [
                    {
                        "id": "ops",
                        "label": "核心操作层",
                        "description": "CNN 三大基础组件",
                        "children": [
                            {"id": "conv", "label": "卷积层 Conv", "description": "提取局部特征，参数共享", "children": [
                                {"id": "kernel", "label": "卷积核 3×3/5×5", "description": "特征检测器", "children": []},
                                {"id": "stride", "label": "步长 Stride", "description": "滑动间隔", "children": []},
                                {"id": "padding", "label": "填充 Padding", "description": "保持尺寸", "children": []},
                            ]},
                            {"id": "pool", "label": "池化层 Pool", "description": "降维+平移不变性", "children": [
                                {"id": "maxpool", "label": "最大池化", "description": "取最大值", "children": []},
                                {"id": "avgpool", "label": "平均池化", "description": "取平均值", "children": []},
                            ]},
                            {"id": "fc", "label": "全连接层 FC", "description": "分类决策", "children": []},
                        ],
                    },
                    {
                        "id": "arch",
                        "label": "经典架构演进",
                        "description": "从简单到深层的 CNN 发展史",
                        "children": [
                            {"id": "lenet", "label": "LeNet-5 (1998)", "description": "手写数字识别鼻祖", "children": []},
                            {"id": "alexnet", "label": "AlexNet (2012)", "description": "深度CNN+ReLU+Dropout", "children": []},
                            {"id": "vgg", "label": "VGG (2014)", "description": "小卷积核堆叠", "children": []},
                            {"id": "resnet", "label": "ResNet (2015)", "description": "残差连接解决退化", "children": []},
                        ],
                    },
                    {
                        "id": "pipeline",
                        "label": "图像分类流程",
                        "description": "从数据到模型部署",
                        "children": [
                            {"id": "aug", "label": "数据增强", "description": "翻转/旋转/色彩", "children": []},
                            {"id": "transfer", "label": "迁移学习", "description": "复用预训练权重", "children": []},
                            {"id": "train", "label": "训练与评估", "description": "损失+准确率监控", "children": []},
                            {"id": "deploy", "label": "部署推理", "description": "模型导出+API", "children": []},
                        ],
                    },
                ],
            }
        },
    },
    {
        "resource_type": "exercise",
        "title": "CNN图像分类专项练习",
        "topic": "卷积神经网络与图像分类",
        "difficulty": "中高级",
        "stage_id": "stage_cnn",
        "task_id": "task_cnn_exercise",
        "summary": "5 道题检验对卷积运算、CNN 架构和图像分类的理解",
        "estimated_minutes": 25,
        "content": {
            "instructions": "请完成以下 5 道关于 CNN 和图像分类的练习。",
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "stem": "输入为 32×32×3 的彩色图像，经过 16 个 5×5 卷积核（步长=1，填充=2）后，输出特征图的尺寸是多少？",
                    "options": [
                        {"key": "A", "text": "28×28×16"},
                        {"key": "B", "text": "30×30×16"},
                        {"key": "C", "text": "32×32×16"},
                        {"key": "D", "text": "32×32×3"},
                    ],
                    "correct_answer": ["C"],
                    "explanation": "输出尺寸 = (32 - 5 + 2×2) / 1 + 1 = 32。填充=2 意味着图像四周各加 2 像素，输入变成 36×36，然后 5×5 核产生 32×32。输出通道数 = 卷积核个数 = 16。所以输出是 32×32×16。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_convolution", "kp_conv_layer"],
                },
                {
                    "id": "q2",
                    "type": "single_choice",
                    "stem": "在 CNN 中，池化层（如 2×2 Max Pooling）的主要作用不包括以下哪一项？",
                    "options": [
                        {"key": "A", "text": "降低特征图的空间尺寸，减少后续层的计算量"},
                        {"key": "B", "text": "提供一定的平移不变性"},
                        {"key": "C", "text": "增加模型的非线性表达能力"},
                        {"key": "D", "text": "保留窗口内的最强特征响应"},
                    ],
                    "correct_answer": ["C"],
                    "explanation": "池化层不包含可学习的参数和激活函数，它只是固定的下采样操作（取最大或平均），不能增加模型的非线性表达能力。非线性来自激活函数（ReLU等）。",
                    "difficulty": "easy",
                    "knowledge_point_ids": ["kp_pooling"],
                },
                {
                    "id": "q3",
                    "type": "single_choice",
                    "stem": "ResNet 引入「残差连接」（Skip Connection）的核心目的是什么？",
                    "options": [
                        {"key": "A", "text": "减少模型的参数量"},
                        {"key": "B", "text": "解决深层网络训练中的退化问题，让梯度能跨越多层直接回传"},
                        {"key": "C", "text": "让模型运行速度更快"},
                        {"key": "D", "text": "自动选择最优的网络深度"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "深层网络面临退化问题：随着层数增加，训练误差不降反升（不是过拟合，是优化困难）。残差连接通过 H(x)=F(x)+x 的形式，让梯度能通过恒等映射直接传回浅层，解决了深层网络的优化问题。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_feature_extraction"],
                },
                {
                    "id": "q4",
                    "type": "single_choice",
                    "stem": "在图像分类任务中，使用「数据增强」的主要目的是？",
                    "options": [
                        {"key": "A", "text": "让模型训练速度更快"},
                        {"key": "B", "text": "增加训练数据多样性，防止过拟合"},
                        {"key": "C", "text": "提高图像的分辨率"},
                        {"key": "D", "text": "替代卷积操作"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "数据增强通过对训练图像进行随机变换（翻转、旋转、颜色扰动等），人为增加了训练数据的多样性。这意味着模型看到的是更多样化的样本，而不是反复看同一批图片，从而减少过拟合风险。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_image_classification"],
                },
                {
                    "id": "q5",
                    "type": "single_choice",
                    "stem": "关于迁移学习（Transfer Learning）在图像分类中的应用，以下说法正确的是？",
                    "options": [
                        {"key": "A", "text": "迁移学习只适用于和原始任务完全相同的新任务"},
                        {"key": "B", "text": "使用在 ImageNet 上预训练的 ResNet 权重，可以显著减少训练数据需求和训练时间"},
                        {"key": "C", "text": "迁移学习意味着不需要任何自己的训练数据"},
                        {"key": "D", "text": "预训练模型的权重只能用于图像分类，不能用于其他任务"},
                    ],
                    "correct_answer": ["B"],
                    "explanation": "迁移学习利用了在大规模数据集（如 ImageNet 100 万张图）上训练的模型权重。浅层卷积核已经学会了检测边缘、纹理等通用特征，可以直接复用。只需要在自己的小数据集上微调（fine-tune）最后的几层，就能获得良好的效果。",
                    "difficulty": "medium",
                    "knowledge_point_ids": ["kp_image_classification", "kp_model_eval"],
                },
            ],
        },
    },
]

# ── 预置错题 ──

DEMO_WRONG_QUESTIONS = [
    {
        "question_id": "wq_lr_001",
        "topic": "学习率",
        "question": "学习率为 0.5 时，模型参数在最优解附近发生震荡。以下哪种方法最可能解决问题？",
        "options": json.dumps(["A. 增大学习率", "B. 减小学习率", "C. 增加训练轮数", "D. 减少训练数据"]),
        "user_answer": "A",
        "correct_answer": "B",
        "explanation": "震荡说明步长过大，应减小学习率。学习率控制每次参数更新的幅度——过大导致在最优解附近来回震荡，过小导致收敛过慢。",
        "wrong_count": 2,
        "status": "unmastered",
    },
    {
        "question_id": "wq_convergence_001",
        "topic": "模型收敛",
        "question": "训练过程中 loss 持续下降但准确率不提高，最可能的原因是什么？",
        "options": json.dumps(["A. 学习率过大", "B. 损失函数与评估指标不一致", "C. 数据量不够", "D. 模型太简单"]),
        "user_answer": "C",
        "correct_answer": "B",
        "explanation": "loss 下降但准确率不提高，通常说明优化的目标（损失函数）与关心的指标（准确率）不完全一致。需要检查损失函数的选择是否匹配任务类型。",
        "wrong_count": 1,
        "status": "reviewing",
    },
    {
        "question_id": "wq_overfit_001",
        "topic": "过拟合",
        "question": "以下哪种方法不能有效缓解过拟合？",
        "options": json.dumps(["A. 增加训练数据", "B. 使用 Dropout", "C. 增加模型参数量", "D. 早停 Early Stopping"]),
        "user_answer": "A",
        "correct_answer": "C",
        "explanation": "增加模型参数量会让模型更复杂，反而加剧过拟合。其他三个选项都是常用的防止过拟合的方法。",
        "wrong_count": 1,
        "status": "unmastered",
    },
]


def init_demo_course(db: Session | None = None) -> dict:
    """初始化演示课程和数据（幂等）。

    可以在 FastAPI 启动事件或脚本中调用。
    重复执行不会创建重复数据。

    Returns:
        {"course": {...}, "path": {...}, "resources": N, "wrong_questions": N, "evaluations": N}
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        result = {}

        # ── 1. 注册课程知识库映射 ──
        KnowledgeService.register_course(
            course_id=COURSE_ID,
            knowledge_base_id=KNOWLEDGE_BASE_ID,
            vector_collection=VECTOR_COLLECTION,
            course_name=COURSE_TITLE,
        )
        logger.info("知识库映射已注册: %s", COURSE_ID)

        # ── 2. 创建/获取演示账号 ──
        from services.auth_service import _hash_password

        user = db.query(User).filter(User.username == DEMO_USERNAME).first()
        if not user:
            user = User(
                id=DEMO_USER_ID,
                username=DEMO_USERNAME,
                password_hash=_hash_password(DEMO_PASSWORD),
                name="演示同学",
                is_demo=True,
            )
            db.add(user)
            db.flush()
            logger.info("演示用户已创建: %s", DEMO_USERNAME)
        else:
            user.is_demo = True
            logger.info("演示用户已存在: %s", DEMO_USERNAME)

        # ── 3. 创建/获取 Student ──
        student = db.query(Student).filter(Student.id == DEMO_STUDENT_ID).first()
        if not student:
            student = Student(id=DEMO_STUDENT_ID, nickname="演示同学")
            db.add(student)
            db.flush()
            logger.info("Student 已创建: %s", DEMO_STUDENT_ID)

        # ── 4. 创建/获取演示课程 ──
        course = db.query(Course).filter(Course.id == COURSE_ID).first()
        if not course:
            course = Course(
                id=COURSE_ID,
                user_id=user.id,
                student_id=DEMO_STUDENT_ID,
                title=COURSE_TITLE,
                goal=COURSE_GOAL,
            )
            db.add(course)
            db.flush()
            logger.info("演示课程已创建: %s", COURSE_TITLE)
        else:
            course.user_id = user.id
            course.student_id = DEMO_STUDENT_ID
            course.title = COURSE_TITLE
            course.goal = COURSE_GOAL
            logger.info("演示课程已存在: %s", COURSE_TITLE)

        # 设置为用户默认课程
        user.active_course_id = COURSE_ID
        db.flush()

        result["course"] = {"id": course.id, "title": course.title, "student_id": course.student_id}

        # ── 5. 创建/更新学习路径（幂等） ──
        scoped_paths = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == DEMO_STUDENT_ID,
                LearningPath.course_id == COURSE_ID,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.version.asc())
            .all()
        )
        completed_paths = []
        for scoped_path in scoped_paths:
            task_rows = db.query(LearningTask).filter(LearningTask.path_id == scoped_path.id).all()
            total_tasks = len({task.task_id for task in task_rows})
            completed_tasks = len({task.task_id for task in task_rows if task.status == "completed"})
            if total_tasks > 0 and completed_tasks >= total_tasks:
                completed_paths.append(scoped_path)
        if completed_paths:
            completed_path = completed_paths[-1]
            for scoped_path in scoped_paths:
                if scoped_path.id == completed_path.id:
                    scoped_path.status = "completed"
                elif scoped_path.status == "active":
                    scoped_path.status = "superseded"
            db.flush()

        existing_path = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == DEMO_STUDENT_ID,
                LearningPath.course_id == COURSE_ID,
                LearningPath.status.in_(("active", "completed")),
            )
            .order_by(LearningPath.status.asc(), LearningPath.version.desc())
            .first()
        )

        if not existing_path:
            path = LearningPath(
                id=str(uuid.uuid4()),
                student_id=DEMO_STUDENT_ID,
                user_id=user.id,
                course_id=COURSE_ID,
                version=1,
                goal="掌握深度学习基础并完成简单图像分类项目",
                stages=json.dumps(DEMO_STAGES, ensure_ascii=False),
                current_stage=2,  # 当前在阶段二
                current_stage_id="stage_gradient_descent",
                estimated_days=sum(stage["estimated_days"] for stage in DEMO_STAGES),
                status="active",
                generation_source="seed",
                generated_by="backend/scripts/init_demo_course.py",
                fallback_used=False,
                generated_at=datetime.datetime.utcnow(),
            )
            db.add(path)
            db.flush()
            logger.info("学习路径已创建: 4个阶段")
            result["path"] = {"id": path.id, "stages": 4, "current_stage": 2}
        else:
            # 启动时不得覆盖真实学习进度；reset_demo_student.py 才负责重置。
            existing_path.user_id = user.id
            existing_path.course_id = COURSE_ID
            existing_path.generation_source = (
                existing_path.generation_source
                if existing_path.generation_source not in (None, "", "legacy")
                else "seed"
            )
            if existing_path.generation_source == "seed":
                existing_path.generated_by = "backend/scripts/init_demo_course.py"
                existing_path.fallback_used = False
            logger.info("学习路径已存在，保留当前任务进度")
            result["path"] = {"id": existing_path.id, "stages": 4, "current_stage": 2}
            path = existing_path

        # ── 6. 预置演示资源（幂等：按 title + course_id 去重） ──
        resource_count = 0
        for res_data in DEMO_RESOURCES:
            existing = (
                db.query(Resource)
                .filter(
                    Resource.title == res_data["title"],
                    Resource.student_id == DEMO_STUDENT_ID,
                )
                .first()
            )
            if not existing:
                resource_obj = Resource(
                    id=str(uuid.uuid4()),
                    student_id=DEMO_STUDENT_ID,
                    course_id=COURSE_ID,
                    type=res_data["resource_type"],
                    title=res_data["title"],
                    topic=res_data["topic"],
                    difficulty=res_data.get("difficulty", "中级"),
                    stage_id=res_data.get("stage_id", ""),
                    task_id=res_data.get("task_id", ""),
                    content=json.dumps(res_data["content"], ensure_ascii=False),
                    trigger_source="demo_seed",
                    trigger_context=json.dumps({"course_id": COURSE_ID}, ensure_ascii=False),
                    generation_source="agent_pre_generated",
                )
                db.add(resource_obj)
                resource_count += 1
        if resource_count:
            logger.info("预置资源已创建: %d 个", resource_count)
        else:
            logger.info("预置资源已存在，跳过")
        result["resources"] = resource_count

        # ── 7. 预置错题（幂等：按 question_id + student_id 去重） ──
        wq_count = 0
        for wq_data in DEMO_WRONG_QUESTIONS:
            existing = (
                db.query(WrongQuestion)
                .filter(
                    WrongQuestion.question_id == wq_data["question_id"],
                    WrongQuestion.student_id == DEMO_STUDENT_ID,
                )
                .first()
            )
            if not existing:
                wq = WrongQuestion(
                    id=str(uuid.uuid4()),
                    student_id=DEMO_STUDENT_ID,
                    question_id=wq_data["question_id"],
                    topic=wq_data["topic"],
                    question=wq_data["question"],
                    question_text=wq_data["question"],
                    options=json.dumps(wq_data["options"], ensure_ascii=False),
                    user_answer=wq_data["user_answer"],
                    correct_answer=wq_data["correct_answer"],
                    explanation=wq_data["explanation"],
                    wrong_count=wq_data.get("wrong_count", 1),
                    status=wq_data.get("status", "unmastered"),
                    last_wrong_at=datetime.datetime.utcnow(),
                )
                db.add(wq)
                wq_count += 1
        if wq_count:
            logger.info("预置错题已创建: %d 道", wq_count)
        result["wrong_questions"] = wq_count

        # ── 8. 评估报告（不再预置硬编码报告）──
        # 第1轮改造：删除预置的假评估分数。
        # demo_student 首次访问评估页时将走真实流水线：
        #   - 数据不足 → 显示数据不足状态，引导完成学习任务
        #   - 数据充分 → 规则计算 + Agent 诊断
        existing_evals = (
            db.query(EvaluationReport)
            .filter(EvaluationReport.student_id == DEMO_STUDENT_ID)
            .count()
        )
        # 删除所有预置的旧硬编码报告
        if existing_evals > 0:
            old_reports = (
                db.query(EvaluationReport)
                .filter(EvaluationReport.student_id == DEMO_STUDENT_ID)
                .all()
            )
            for old in old_reports:
                db.delete(old)
            logger.info("已删除 %d 份旧硬编码评估报告", existing_evals)
        eval_count = 0
        result["evaluations"] = 0

        # ── 9. 预置学习记录（可追溯的真实行为数据）──
        existing_records = (
            db.query(LearningRecord)
            .filter(LearningRecord.student_id == DEMO_STUDENT_ID)
            .count()
        )
        record_count = 0
        if existing_records < 15:
            now = datetime.datetime.utcnow()
            # 构造足够通过数据充分性门槛的学习行为（≥10条记录 + ≥5道答题）
            demo_behaviors = [
                # (days_ago, action, topic, score, time_spent)
                # 任务完成记录
                (0, "complete", "梯度下降", None, 2400),
                (1, "complete", "学习率", None, 1800),
                (2, "complete", "损失函数", None, 1500),
                (3, "complete", "过拟合与欠拟合", None, 2100),
                # 答题记录
                (0, "answer", "梯度下降", 0.80, 600),
                (0, "answer", "学习率", 0.60, 450),
                (1, "answer", "损失函数", 0.90, 300),
                (1, "answer", "学习率", 0.50, 500),
                (2, "answer", "过拟合", 0.85, 400),
                (2, "answer", "梯度下降", 0.70, 350),
                (3, "answer", "损失函数", 0.95, 300),
                (3, "answer", "过拟合", 0.45, 400),
                # 测评记录
                (1, "self_eval", "梯度下降", 0.72, 1200),
                # 复习记录
                (0, "review", "学习率", None, 900),
            ]
            for days_ago, action, topic, score, time_spent in demo_behaviors:
                created = now - datetime.timedelta(days=days_ago, hours=days_ago)
                existing_same = (
                    db.query(LearningRecord)
                    .filter(
                        LearningRecord.student_id == DEMO_STUDENT_ID,
                        LearningRecord.action == action,
                        LearningRecord.topic == topic,
                    )
                    .first()
                )
                if not existing_same:
                    record = LearningRecord(
                        id=str(uuid.uuid4()),
                        student_id=DEMO_STUDENT_ID,
                        action=action,
                        topic=topic,
                        score=score,
                        time_spent=time_spent,
                        created_at=created,
                    )
                    db.add(record)
                    record_count += 1
            logger.info("预置学习记录: %d 条", record_count)

        db.commit()
        from deps import planner_service

        planner_service.ensure_normalized_entities(db, path)
        logger.info("演示数据初始化完成（幂等）")

        return result

    finally:
        if close_db:
            db.close()


# ── 命令行入口 ──

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    result = init_demo_course()
    print("\n✅ 演示课程初始化完成:")
    print(f"   课程: {result.get('course', {}).get('title', 'N/A')}")
    print(f"   学习路径: {result.get('path', {}).get('stages', 0)} 个阶段")
    print(f"   预置资源: {result.get('resources', 0)} 个")
    print(f"   预置错题: {result.get('wrong_questions', 0)} 道")
    print(f"   评估报告: {result.get('evaluations', 0)} 份")
    print(f"\n   演示账号: {DEMO_USERNAME}")
    print(f"   演示密码: {DEMO_PASSWORD}")
    print(f"   默认课程: {COURSE_TITLE}")
