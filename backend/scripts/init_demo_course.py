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
from models.learning_path import LearningPath
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

# ── 预置演示资源 ──

DEMO_RESOURCES = [
    {
        "resource_type": "document",
        "title": "梯度下降核心讲义",
        "topic": "梯度下降",
        "difficulty": "中级",
        "stage_id": "stage_gradient_descent",
        "summary": "深入讲解损失函数、梯度计算、参数更新和学习率调优",
        "estimated_minutes": 30,
        "content": {
            "learning_objectives": ["理解损失函数的作用", "掌握梯度下降参数更新公式", "能分析学习率影响"],
            "sections": [
                {
                    "heading": "1. 损失函数",
                    "paragraphs": ["损失函数衡量模型预测值与真实值的差距。常见损失函数包括均方误差(MSE)和交叉熵(Cross-Entropy)。"],
                    "examples": ["线性回归使用 MSE，分类问题使用交叉熵"],
                    "key_points": ["损失函数越小，模型拟合越好", "不同任务需要不同的损失函数"],
                },
                {
                    "heading": "2. 梯度与梯度下降",
                    "paragraphs": ["梯度是损失函数对参数的偏导数向量，指向损失上升最快的方向。梯度下降沿负梯度方向更新参数。"],
                    "examples": ["参数更新公式: θ = θ - α∇J(θ)"],
                    "key_points": ["梯度指向损失上升方向", "沿负梯度方向损失下降最快"],
                },
                {
                    "heading": "3. 学习率",
                    "paragraphs": ["学习率 α 控制每次参数更新的步长。过大导致震荡不收敛，过小导致收敛缓慢。"],
                    "examples": ["α=0.01 是常用初始值", "可使用学习率衰减策略"],
                    "key_points": ["学习率是最重要的超参数之一", "过大震荡，过小缓慢"],
                },
            ],
            "summary": "梯度下降是深度学习最核心的优化算法，理解损失函数、梯度和学习率三者关系是掌握模型训练的关键。",
            "common_mistakes": ["混淆损失函数和评估指标", "学习率设置过大导致不收敛", "忽略梯度消失/爆炸问题"],
        },
    },
    {
        "resource_type": "mindmap",
        "title": "梯度下降知识导图",
        "topic": "梯度下降",
        "difficulty": "中级",
        "stage_id": "stage_gradient_descent",
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
                goal="掌握深度学习基础并完成简单图像分类项目",
            )
            db.add(course)
            db.flush()
            logger.info("演示课程已创建: %s", COURSE_TITLE)
        else:
            logger.info("演示课程已存在: %s", COURSE_TITLE)

        # 设置为用户默认课程
        user.active_course_id = COURSE_ID
        db.flush()

        result["course"] = {"id": course.id, "title": course.title, "student_id": course.student_id}

        # ── 5. 创建/更新学习路径（幂等） ──
        existing_path = (
            db.query(LearningPath)
            .filter(
                LearningPath.student_id == DEMO_STUDENT_ID,
                LearningPath.status == "active",
            )
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
                    type=res_data["resource_type"],
                    title=res_data["title"],
                    topic=res_data["topic"],
                    difficulty=res_data.get("difficulty", "中级"),
                    stage_id=res_data.get("stage_id", ""),
                    content=json.dumps(res_data["content"], ensure_ascii=False),
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

        # ── 8. 预置评估报告（幂等：按 student_id 检查） ──
        existing_evals = (
            db.query(EvaluationReport)
            .filter(EvaluationReport.student_id == DEMO_STUDENT_ID)
            .count()
        )
        eval_count = 0
        if existing_evals < 2:
            for i in range(2 - existing_evals):
                now = datetime.datetime.utcnow()
                days_ago = (2 - i) * 3
                created = now - datetime.timedelta(days=days_ago)
                eval_report = EvaluationReport(
                    id=str(uuid.uuid4()),
                    student_id=DEMO_STUDENT_ID,
                    overall_score=72 if i == 0 else 68,
                    dimensions=json.dumps({
                        "knowledge_mastery": 70,
                        "test_accuracy": 68,
                        "task_completion": 35,
                        "learning_consistency": 80,
                    }),
                    weak_topics=json.dumps(["学习率选择", "模型收敛判断"]),
                    suggestions=json.dumps([
                        "针对'学习率选择'知识点完成专项练习",
                        "通过对比实验加深对模型收敛条件的理解",
                    ]),
                    review_plan=json.dumps([]),
                    source_snapshot=json.dumps({"course_id": COURSE_ID}),
                    created_at=created,
                    updated_at=created,
                )
                db.add(eval_report)
                eval_count += 1
            logger.info("预置评估报告已创建: %d 份", eval_count)
        else:
            logger.info("评估报告已存在: %d 份", existing_evals)
        result["evaluations"] = max(existing_evals, 2)

        # ── 9. 预置学习记录（使统计数据有意义） ──
        existing_records = (
            db.query(LearningRecord)
            .filter(LearningRecord.student_id == DEMO_STUDENT_ID)
            .count()
        )
        record_count = 0
        if existing_records < 10:
            # 创建一些学习记录以支持进度统计
            for days_ago in range(4):
                created = datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)
                for action in ["complete", "answer"]:
                    existing_same_day = (
                        db.query(LearningRecord)
                        .filter(
                            LearningRecord.student_id == DEMO_STUDENT_ID,
                            LearningRecord.action == action,
                        )
                        .first()
                    )
                    if not existing_same_day:
                        record = LearningRecord(
                            id=str(uuid.uuid4()),
                            student_id=DEMO_STUDENT_ID,
                            action=action,
                            topic="梯度下降" if days_ago % 2 == 0 else "学习率",
                            score=0.75 if days_ago % 2 == 0 else 0.6,
                            time_spent=1800 if action == "complete" else 900,
                            created_at=created,
                        )
                        db.add(record)
                        record_count += 1

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
