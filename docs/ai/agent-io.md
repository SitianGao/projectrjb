
# Agent 输入输出设计

## 1. 文档目的

本文档用于定义系统中各智能体（Agent）的职责边界、输入输出结构及协作关系，作为后续系统设计、接口实现、联调测试和时序图细化的基础。

本项目围绕“学生画像构建—资源生成—学习路径规划—智能辅导—学习效果评估”五大核心功能，设计如下智能体：

- Profile Agent（学生画像智能体）
- Planner Agent（学习规划智能体）
- Resource Agent（资源生成/推荐智能体）
- Tutor Agent（学习辅导智能体）
- Evaluation Agent（学习效果评估智能体）
- Coordinator Agent（协调智能体，可选但建议加入）

---

## 2. 设计原则

### 2.1 职责单一
每个 Agent 只负责一类核心任务，避免逻辑重叠。

### 2.2 输入输出结构化
尽量采用 JSON 风格结构，便于前后端对接与任务编排。

### 2.3 支持可追踪与可审计
所有关键任务保留如下字段：

- `task_id`
- `correlation_id`
- `user_id`
- `timestamp`
- `confidence`
- `sources`

### 2.4 支持异步任务机制
对于资源生成、评估分析等长耗时任务，建议采用异步任务模式，由协调智能体和任务队列统一调度。

---

## 3. 通用字段约定

## 3.1 通用输入字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| user_id | string | 用户唯一标识 |
| session_id | string | 当前会话 ID |
| task_id | string | 当前任务 ID |
| correlation_id | string | 请求链路追踪 ID |
| timestamp | string | 请求发起时间 |
| profile_id | string | 学生画像 ID（如已存在） |

## 3.2 通用输出字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| status | string | 执行状态，如 success / partial / failed |
| message | string | 结果说明 |
| confidence | float | 输出结果置信度 |
| sources | array | 内容来源或知识依据 |
| updated_at | string | 更新时间 |
| next_action | string | 推荐后续动作 |

---

## 4. Agent 协作关系总览

系统总体协作逻辑如下：

1. 学生与系统进行自然语言对话
2. Profile Agent 根据对话和学习记录构建学生画像
3. Planner Agent 根据学生画像与课程知识结构规划学习路径
4. Resource Agent 根据路径与知识短板生成个性化学习资源
5. Tutor Agent 在学习过程中提供实时辅导与答疑
6. Evaluation Agent 根据行为、练习和反馈评估学习效果
7. 评估结果回流至 Planner Agent 与 Profile Agent，形成动态闭环优化

---

## 5. Profile Agent（学生画像智能体）

## 5.1 职责说明

Profile Agent 负责通过自然语言对话和学习数据分析，自动构建动态学生画像。

主要职责：

- 识别学生学习目标
- 判断学生知识基础
- 分析学习偏好与认知风格
- 识别薄弱点与易错点
- 动态更新学生画像

## 5.2 输入

### 输入来源
- 学生多轮对话内容
- 历史学习记录
- 行为日志
- 测试结果摘要（可选）

### 输入示例

```json
{
  "user_id": "u001",
  "session_id": "s001",
  "task_id": "t_profile_001",
  "correlation_id": "corr_001",
  "timestamp": "2026-04-01T16:00:00",
  "utterances": [
    "我想学习人工智能基础",
    "我编程还可以，但是数学一般",
    "我更喜欢图解和案例"
  ],
  "learning_history": [
    "已学习 Python 基础",
    "完成线性代数入门练习"
  ],
  "behavior_logs": [
    "偏好视频资源",
    "练习题完成率 70%"
  ]
}
5.3 输出
输出内容
至少生成以下 6 个以上维度：

知识基础
学习目标
学习历史
认知风格
易错点偏好
兴趣方向
学习节奏偏好
资源偏好
输出示例
{
  "status": "success",
  "profile_id": "p001",
  "profile": {
    "knowledge_base": "初级",
    "learning_goal": "人工智能基础入门",
    "learning_history": "具备 Python 基础，线性代数基础一般",
    "cognitive_style": "偏好图解和案例",
    "error_preference": "数学推导类知识容易出错",
    "interest_area": "人工智能应用案例",
    "resource_preference": "视频+图文",
    "pace_preference": "中速"
  },
  "confidence": 0.91,
  "sources": ["dialogue", "learning_history", "behavior_logs"],
  "updated_at": "2026-04-01T16:00:02",
  "next_action": "调用 Planner Agent 生成学习路径"
}
5.4 说明
支持随学随新，画像应可增量更新
建议保存 version 字段，支持乐观锁更新
输出结果将作为 Planner Agent、Resource Agent、Tutor Agent 的基础输入
6. Planner Agent（学习规划智能体）
6.1 职责说明
Planner Agent 根据学生画像、课程知识体系和学习进度，规划个性化学习路径与阶段任务。

主要职责：

分析当前学习阶段
拆分学习目标
规划学习顺序
推荐阶段性任务
为资源生成提供路线依据
6.2 输入
输入来源
Profile Agent 输出画像
课程知识库目录/课程大纲
当前学习进度
学习效果评估结果（可选）
输入示例
{
  "user_id": "u001",
  "task_id": "t_plan_001",
  "correlation_id": "corr_002",
  "profile": {
    "knowledge_base": "初级",
    "learning_goal": "人工智能基础入门",
    "cognitive_style": "偏好图解和案例",
    "error_preference": "数学推导类知识容易出错"
  },
  "course_outline": [
    "人工智能概述",
    "机器学习基础",
    "神经网络基础",
    "深度学习应用",
    "综合实践"
  ],
  "current_progress": {
    "completed_topics": ["人工智能概述"],
    "mastery": {
      "人工智能概述": 0.85,
      "机器学习基础": 0.30
    }
  }
}
6.3 输出
输出内容
个性化学习路径
阶段目标
学习步骤
每阶段推荐资源类型
输出示例
{
  "status": "success",
  "plan_id": "plan001",
  "learning_path": [
    {
      "stage": 1,
      "topic": "机器学习基础",
      "goal": "理解监督学习与无监督学习的基本概念",
      "estimated_time": "3天",
      "recommended_resource_types": [
        "讲解文档",
        "思维导图",
        "基础练习题",
        "案例讲解视频"
      ]
    },
    {
      "stage": 2,
      "topic": "神经网络基础",
      "goal": "掌握感知机、前馈网络基本原理",
      "estimated_time": "4天",
      "recommended_resource_types": [
        "图文讲解",
        "PPT",
        "代码案例"
      ]
    }
  ],
  "confidence": 0.88,
  "sources": ["profile", "course_outline", "current_progress"],
  "next_action": "调用 Resource Agent 生成阶段1学习资源"
}
6.4 说明
学习路径应体现“先基础、后进阶”的逻辑
支持后续由 Evaluation Agent 的评估结果触发动态调整
规划结果应明确到“阶段”或“知识点级别”
7. Resource Agent（资源生成智能体）
7.1 职责说明
Resource Agent 根据学习路径、学生画像和课程知识库，生成个性化、多模态学习资源。

主要职责：

检索课程知识内容
生成讲义、笔记、导图、题目、PPT、代码案例等
依据学生特点调整内容表达方式
输出结构化资源结果
7.2 输入
输入来源
Planner Agent 的阶段任务
Profile Agent 的学生画像
课程知识库检索结果
资源生成类型要求
输入示例
{
  "user_id": "u001",
  "task_id": "t_resource_001",
  "correlation_id": "corr_003",
  "topic": "机器学习基础",
  "resource_types": [
    "lecture_note",
    "mind_map",
    "quiz",
    "ppt_outline",
    "code_case"
  ],
  "profile": {
    "knowledge_base": "初级",
    "cognitive_style": "偏好图解和案例",
    "resource_preference": "视频+图文"
  },
  "knowledge_context": [
    "教材第2章：机器学习基础",
    "课程PPT第2讲",
    "案例讲义：分类与聚类示例"
  ]
}
7.3 输出
输出资源类型建议
至少覆盖以下 5 类资源中的多项：

课程讲解文档
知识点思维导图
练习题与测试题
拓展阅读材料
多模态教学内容脚本
代码实操案例
PPT 大纲/讲稿
输出示例
{
  "status": "success",
  "resources": [
    {
      "resource_id": "r001",
      "type": "lecture_note",
      "title": "机器学习基础讲解文档",
      "format": "markdown",
      "url": "/resources/r001.md",
      "confidence": 0.92
    },
    {
      "resource_id": "r002",
      "type": "mind_map",
      "title": "机器学习基础思维导图",
      "format": "svg",
      "url": "/resources/r002.svg",
      "confidence": 0.89
    },
    {
      "resource_id": "r003",
      "type": "quiz",
      "title": "机器学习基础练习题",
      "format": "json",
      "url": "/resources/r003.json",
      "confidence": 0.93
    },
    {
      "resource_id": "r004",
      "type": "code_case",
      "title": "KNN 分类案例代码",
      "format": "python",
      "url": "/resources/r004.py",
      "confidence": 0.90
    }
  ],
  "sources": [
    "教材第2章",
    "课程PPT第2讲",
    "案例讲义"
  ],
  "next_action": "推送资源至前端并通知用户"
}
7.4 说明
Resource Agent 是比赛核心亮点之一
输出内容应体现“个性化”和“多模态”
输出建议带 sources 字段，方便防幻觉与引用展示
8. Tutor Agent（学习辅导智能体）
8.1 职责说明
Tutor Agent 面向学生学习过程中的即时问题，提供问答、讲解、纠错和学习建议。

主要职责：

回答学生提问
对复杂知识点做简化解释
提供错题分析与针对性建议
结合学生画像调整表达风格
8.2 输入
输入来源
学生问题
Profile Agent 的学生画像
RAG 检索结果
当前学习上下文
输入示例
{
  "user_id": "u001",
  "task_id": "t_tutor_001",
  "correlation_id": "corr_004",
  "question": "监督学习和无监督学习有什么区别？",
  "profile": {
    "knowledge_base": "初级",
    "cognitive_style": "偏好图解和案例"
  },
  "retrieved_context": [
    "教材2.1节：监督学习定义",
    "教材2.2节：无监督学习定义",
    "课程讲义：分类与聚类案例"
  ]
}
8.3 输出
输出内容
文本讲解
图解需求标识
视频脚本需求标识
学习建议
输出示例
{
  "status": "success",
  "answer": {
    "text": "监督学习使用带标签的数据进行训练，例如已知图片是猫还是狗；无监督学习则不依赖标签，而是从数据中自动发现规律，例如聚类分析。",
    "diagram_needed": true,
    "video_explain_needed": false,
    "learning_tip": "建议结合分类与聚类案例一起理解这两个概念。"
  },
  "confidence": 0.87,
  "sources": [
    "教材2.1节",
    "教材2.2节",
    "课程讲义案例"
  ],
  "next_action": "如用户继续追问，可生成图解说明"
}
8.4 说明
Tutor Agent 应明显体现“智能辅导”特色
输出风格应尽量符合学生认知水平
若置信度过低，应触发降级或人工审核机制
9. Evaluation Agent（学习效果评估智能体）
9.1 职责说明
Evaluation Agent 负责根据学生学习行为、练习结果和资源使用情况，评估学习效果并提出优化建议。

主要职责：

跟踪学习行为
分析掌握程度
识别薄弱知识点
给出改进建议
反馈给 Planner Agent 进行路径优化
9.2 输入
输入来源
学生学习记录
练习测试结果
资源使用反馈
TutorAgent 交互记录（可选）
输入示例
{
  "user_id": "u001",
  "task_id": "t_eval_001",
  "correlation_id": "corr_005",
  "quiz_result": {
    "score": 78,
    "wrong_topics": ["监督学习应用场景"]
  },
  "behavior_logs": [
    "视频观看完成率 90%",
    "练习题完成率 75%",
    "思维导图浏览 1 次"
  ],
  "resource_usage": [
    "lecture_note",
    "quiz",
    "video"
  ]
}
9.3 输出
输出内容
学习进度评估
掌握程度分析
薄弱点分析
优化建议
输出示例
{
  "status": "success",
  "assessment": {
    "progress": 0.45,
    "mastery_level": "中等",
    "weak_points": ["监督学习应用场景"],
    "learning_efficiency": "较高"
  },
  "recommendations": [
    "补充监督学习案例练习",
    "推送监督学习应用场景图解",
    "适当增加综合判断题训练"
  ],
  "confidence": 0.90,
  "sources": [
    "quiz_result",
    "behavior_logs",
    "resource_usage"
  ],
  "next_action": "将评估结果回传给 Planner Agent 调整学习计划"
}
9.4 说明
Evaluation Agent 是学习闭环优化的关键
输出必须能被 Planner Agent 消费
建议弱项细化到章节/知识点级别
10. Coordinator Agent（协调智能体，建议加入）
10.1 职责说明
Coordinator Agent 不直接承担教学分析任务，而是作为系统编排与调度中心，负责：

接收外部请求
拆分主任务与子任务
调度各 Agent
聚合结果
返回任务状态与进度
10.2 输入示例
{
  "task_type": "generate_learning_resources",
  "user_id": "u001",
  "profile_id": "p001",
  "topic": "机器学习基础",
  "resource_types": [
    "lecture_note",
    "mind_map",
    "quiz"
  ]
}
10.3 输出示例
{
  "task_id": "t_master_001",
  "status": "running",
  "sub_tasks": [
    "t_profile_001",
    "t_plan_001",
    "t_resource_001"
  ],
  "progress": 0.4,
  "message": "资源生成中"
}
10.4 说明
在比赛答辩中，加入 Coordinator Agent 有助于体现“多智能体协同架构”
可与 TaskQueue、WebSocket、异步任务结合实现更清晰的工程逻辑
11. Agent 协作闭环总结
本系统可概括为如下闭环：

Profile Agent 构建学生画像
Planner Agent 规划学习路径
Resource Agent 生成个性化资源
Tutor Agent 提供实时辅导
Evaluation Agent 评估学习效果
评估结果回流，推动画像更新与路径优化
该设计既满足赛题的功能要求，又能体现：

多智能体协作
个性化资源生成
智能辅导
学习效果闭环优化
12. 后续可扩展内容
后续可在此基础上继续补充：

各 Agent 的 Prompt 模板设计
各 Agent 对应 API 接口定义
Agent 任务队列消息格式
Agent 失败重试与降级策略
Agent 与数据库/向量库的交互设计