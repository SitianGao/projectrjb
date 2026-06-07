# 系统开发说明书

> **项目**：EduAgent — 基于大模型的个性化学习资源生成与学习多智能体系统
> **赛题**：第15届软件杯 A3 | 出题方：科大讯飞

---

## 1. 系统概述

### 1.1 项目定位

本项目构建基于大模型和多智能体协同的个性化学习资源智能体平台。系统围绕"学生画像 → 学习路径规划 → 资源生成 → 智能辅导 → 学习评估"的完整闭环，实现高等教育场景下的个性化学习支持。

### 1.2 核心功能

| 功能模块 | 说明 |
|----------|------|
| 对话式学生画像构建 | 通过自然语言对话获取学生信息，构建 6 维动态画像 |
| 多智能体协同资源生成 | Profile/Planner/Resource/Tutor/Evaluate 五个 Agent 协同工作 |
| 个性化学习路径规划 | 基于画像生成分阶段学习路径，支持动态调整 |
| 智能辅导问答 | 流式对话辅导，支持多模态回答（文本/图解/代码） |
| 学习效果评估 | 多维评估 + 反馈闭环，自动调整学习策略 |
| 多模态资源生成 | 课程文档、思维导图、练习题、代码案例、PPT、图表 |

### 1.3 用例图（学生视角）

下图展示了学生用户与本系统的核心交互场景，包括画像构建、路径规划、资源生成、智能辅导和学习评估五个主要用例。

![学生视角用例图](images/use-case.png)

*图 1-1：学生视角用例图。学生通过对话式画像构建初始化个人学习档案，随后系统生成个性化学习路径与配套资源。学生在学习过程中可随时进行智能问答，系统根据学习记录进行评估并动态调整学习计划。*

---

## 2. 系统架构

### 2.1 五层架构

```
┌─────────────────────────────────────────────────────────────┐
│  部署层                                                     │
│  Docker + docker-compose + Nginx                            │
├─────────────────────────────────────────────────────────────┤
│  前端层         React 19 + Vite + Ant Design 5              │
│               + Vercel AI SDK + markmap + Mermaid           │
├─────────────────────────────────────────────────────────────┤
│  后端层         FastAPI + uvicorn + SSE                     │
│               异步流式、Swagger 自动文档、CORS                │
├─────────────────────────────────────────────────────────────┤
│  AI 层          LangChain + LangGraph（Agent 编排）          │
│                + 讯飞星火 Spark 4.0 + ChromaDB + RAG        │
├─────────────────────────────────────────────────────────────┤
│  数据层         SQLite（开发）/ MySQL（提交）                 │
│                + Redis（缓存/异步任务，可选）                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术架构图

```
浏览器 ──HTTP/SSE──▶ Nginx ──▶ FastAPI ──▶ AgentOrchestrator
                                              │
                    ┌──────────────────────────┼──────────────────────────┐
                    │              │           │           │              │
                    ▼              ▼           ▼           ▼              ▼
              ProfileAgent  PlannerAgent ResourceAgent TutorAgent EvaluateAgent
                    │              │           │           │              │
                    └──────────────┴───────────┴───────────┴──────┬───────┘
                                                                  │
                                                    ┌─────────────┴─────────────┐
                                                    ▼                           ▼
                                               LLMClient                   RAG Pipeline
                                          (星火/DeepSeek)              (ChromaDB + Embedding)
                                                    │                           │
                                                    ▼                           ▼
                                              SQLite/MySQL              知识库文档
```

### 2.2a 系统架构图

![系统架构图](images/architecture.png)

*图 2-1：系统整体架构图。系统采用五层架构设计——前端层（React + Ant Design）、后端层（FastAPI）、AI 层（LangGraph Agent 编排 + 讯飞星火 LLM + ChromaDB RAG）、数据层（SQLite/MySQL）和部署层（Docker + Nginx）。各层之间通过 HTTP/SSE 协议通信，数据从上到下逐层传递。*

### 2.3 数据流

```
1. 用户在前端输入 → POST /api/profile/chat (SSE)
2. FastAPI 路由 → ProfileAgent.run()
3. ProfileAgent 调用 LLMClient.chat_stream() → 讯飞星火 API
4. 流式返回画像 JSON → 存入数据库
5. PlannerAgent + ResourceAgent 并行执行
6. 生成学习路径 + 学习资源 → 推送给前端渲染
7. 用户触发 TutorAgent（问答）或 EvaluateAgent（评估）
8. 评估结果反馈 → 调整路径和资源 → 闭环
```

![顶层和一层数据流图](images/dfd-level0&1.png)

*图 2-2：顶层数据流图（Level 0）和一层数据流图（Level 1）。顶层 DFD 展示了系统与外部实体（学生用户）之间的数据交互——学生输入学习描述，系统返回画像、路径、资源和评估报告。一层 DFD 将系统分解为画像管理、路径规划、资源生成、智能辅导和学习评估五个核心处理模块，以及学生信息库、知识库和学习记录库三个数据存储。*

---

## 3. 技术选型

### 3.1 选型总表

| 层面 | 技术 | 版本 | 选型理由 |
|------|------|------|----------|
| **大模型（主）** | 讯飞星火 Spark | 4.0 | 赛题方是讯飞，使用星火有加分 |
| **大模型（备）** | DeepSeek | V3 | 国内好用、便宜、OpenAI 兼容接口 |
| **后端框架** | FastAPI | 0.115 | 原生异步、SSE 流式、自动 Swagger 文档 |
| **Agent 编排** | LangGraph | 0.2 | 状态图编排、条件分支、并行支持 |
| **LLM 调用** | LangChain | 0.3 | 统一 LLM 接口、Prompt 模板 |
| **前端框架** | React + Vite | 19 / 6 | 生态最大、AI 工具代码生成质量最高 |
| **UI 组件库** | Ant Design | 5.22 | 中文友好、组件丰富、业务组件现成 |
| **AI SDK** | Vercel AI SDK | 4.0 | 内置 useChat hook，5 行代码搞定流式对话 |
| **数据库** | SQLite → MySQL | - | SQLite 零配置开发，提交切 MySQL |
| **向量数据库** | ChromaDB | 0.5 | 最轻量，pip install 即用，无需 Docker |
| **嵌入模型** | sentence-transformers | 3.0 | paraphrase-multilingual-MiniLM-L12-v2 |
| **思维导图** | markmap | 0.18 | Markdown 列表直接渲染为思维导图 |
| **图表** | Mermaid.js | 11 | 文本生成流程图/时序图 |
| **PPT 生成** | python-pptx | 1.0 | 简单 PPT 生成，LLM 输出大纲即可 |
| **内容安全** | 关键词过滤 + Prompt 约束 | - | 双重过滤，无需额外服务 |
| **部署** | Docker + docker-compose | - | 评委一键启动 |

### 3.2 与赛题技术要求的对应

| 赛题要求 | 实现方式 |
|----------|----------|
| 大模型驱动 | 讯飞星火 Spark 4.0 为主力模型 |
| 多智能体协同 | LangGraph 状态图编排，5 个 Agent 并行协作 |
| 多模态生成 | Markdown + 思维导图(markmap) + 图表(Mermaid) + PPT(python-pptx) |
| 流式输出 | FastAPI SSE + Vercel AI SDK |
| 内容安全 | 双层过滤：敏感词库 + System Prompt 约束 |
| 防幻觉 | RAG 知识增强 + 来源标注 + Prompt 约束 |

---

## 4. 模块设计

### 4.1 后端模块

```
backend/
├── app.py                    主入口，注册路由和中间件
├── config.py                 配置管理（数据库URL、API Key等）
│
├── api/                      路由层 — 处理 HTTP 请求/响应
│   ├── profile_api.py        /api/profile/* 学生画像
│   ├── planner_api.py        /api/planner/* 学习路径
│   ├── resource_api.py       /api/resource/* 学习资源
│   ├── tutor_api.py          /api/tutor/* 智能辅导
│   ├── evaluate_api.py       /api/evaluate/* 学习评估
│   └── task_api.py           /api/task/* 异步任务状态
│
├── agents/                   AI 层 — 核心智能逻辑
│   ├── base_agent.py         Agent 基类（流式调用 + 重试 + 日志）
│   ├── llm_client.py         LLM 统一封装（星火 + DeepSeek 自动切换）
│   ├── profile_agent.py      学生画像 Agent
│   ├── planner_agent.py      学习规划 Agent
│   ├── resource_agent.py     资源生成 Agent
│   ├── tutor_agent.py        智能辅导 Agent
│   ├── evaluate_agent.py     学习评估 Agent
│   └── orchestrator.py       Agent 编排器（LangGraph 状态图）
│
├── rag/                      RAG 检索管线
│   ├── embedding.py          文本转向量
│   ├── vector_store.py       ChromaDB 操作封装
│   ├── retriever.py          检索逻辑
│   └── knowledge_loader.py   知识数据导入
│
├── models/                   数据模型层 — SQLAlchemy ORM
│   ├── student.py            Student + StudentProfile
│   ├── learning_path.py      LearningPath
│   ├── resource.py           Resource
│   └── evaluation.py         LearningRecord
│
├── services/                 业务逻辑层 — API 与 Agent 的桥梁
├── safety/                   内容安全
│   └── content_filter.py     敏感词 + 安全校验
└── utils/                    工具函数
    ├── logger.py             日志
    └── task_manager.py       异步任务管理
```

### 4.2 前端模块

```
frontend/src/
├── api/                      后端 API 调用封装
│   ├── client.js             axios 实例 + 基础配置
│   ├── profile.js            画像 API
│   ├── planner.js            规划 API
│   ├── resource.js           资源 API
│   ├── tutor.js              辅导 API
│   └── evaluate.js           评估 API
│
├── pages/                    页面组件
│   ├── ProfilePage.jsx       学生画像页（对话 + 画像卡片）
│   ├── LearningPathPage.jsx  学习路径页（时间线/步骤条）
│   ├── ResourcePage.jsx      学习资源页（资源卡片列表）
│   ├── TutorPage.jsx         智能辅导页（问答聊天界面）
│   └── EvaluatePage.jsx      学习评估页（进度 + 评分图表）
│
├── components/               可复用组件
│   ├── ChatBox.jsx           通用对话组件（流式显示）
│   ├── ProfileCard.jsx       画像卡片
│   ├── ResourceCard.jsx      资源卡片
│   ├── PathTimeline.jsx      学习路径时间线
│   ├── MindMapViewer.jsx     思维导图查看器（markmap）
│   ├── MermaidChart.jsx      图表渲染器（mermaid）
│   ├── MarkdownRenderer.jsx  Markdown 渲染器
│   ├── QuizCard.jsx          练习题卡片
│   └── ProgressBar.jsx       生成进度条
│
└── hooks/                    自定义 Hooks
    ├── useChat.js            对话 Hook（Vercel AI SDK）
    └── useTaskStatus.js      异步任务轮询 Hook
```

### 4.3 AI/RAG 模块（队员B）

```
backend/agents/               Agent 核心逻辑
├── profile_agent.py          System Prompt 设计 + 画像提取逻辑
├── planner_agent.py          学习路径生成逻辑
├── resource_agent.py         多类型资源生成逻辑
├── tutor_agent.py            多风格解释生成逻辑
└── evaluate_agent.py         多维评估 + 遗忘曲线计算

backend/rag/                  RAG 检索管线
├── embedding.py              文本 → 向量（sentence-transformers）
├── vector_store.py           ChromaDB CRUD 操作
├── retriever.py              语义检索 + 相似度排序
└── knowledge_loader.py       Markdown/JSON 知识数据导入

backend/safety/               内容安全
└── content_filter.py         敏感词过滤 + 输入输出校验
```

---

## 5. 数据库设计

### 5.1 ER 图（逻辑）

```
students 1 ──── * student_profiles    (一个学生多个画像版本)
students 1 ──── * learning_paths      (一个学生多个路径版本)
students 1 ──── * resources           (一个学生多个资源)
students 1 ──── * learning_records    (一个学生多条学习记录)
learning_paths 1 ──── * resources     (一个路径关联多个资源)
```

![ER图](images/er-diagram.png)

*图 5-1：数据库 ER 图。系统包含 5 张核心表：students（学生）与 student_profiles（画像）、learning_paths（学习路径）、resources（学习资源）、learning_records（学习记录）之间为一对多关系。student_profiles 中的 memory_strength 字段存储各知识点的记忆强度，支撑遗忘曲线驱动的间隔复习功能。*

### 5.2 表结构

#### students — 学生表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| nickname | VARCHAR(100) | 学生昵称 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### student_profiles — 学生画像表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| student_id | VARCHAR(36) FK | 关联学生 |
| version | INTEGER | 画像版本号（动态更新+1） |
| knowledge_level | TEXT | 知识基础 |
| learning_goal | TEXT | 学习目标 |
| learning_history | TEXT | 学习历史（JSON 数组） |
| cognitive_style | TEXT | 认知风格 |
| weakness | TEXT | 薄弱点（JSON 数组） |
| interest | TEXT | 兴趣方向（JSON 数组） |
| memory_strength | TEXT | 各知识点记忆强度 JSON（创新点） |
| completeness | REAL | 画像完整度 0-1 |
| created_at | DATETIME | 创建时间 |

#### learning_paths — 学习路径表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| student_id | VARCHAR(36) FK | 关联学生 |
| version | INTEGER | 路径版本号 |
| goal | TEXT | 学习总目标 |
| stages | TEXT | 阶段列表（JSON） |
| current_stage | INTEGER | 当前所在阶段 |
| status | VARCHAR(20) | active / completed / paused |

#### resources — 学习资源表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| student_id | VARCHAR(36) FK | 关联学生 |
| path_id | INTEGER FK | 关联学习路径 |
| type | VARCHAR(30) | document / mindmap / exercise / code / reading / ppt |
| title | VARCHAR(200) | 资源标题 |
| content | TEXT | Markdown/JSON 内容 |
| topic | VARCHAR(100) | 知识点主题 |
| difficulty | VARCHAR(20) | 初级 / 中级 / 高级 |
| is_review | BOOLEAN | 是否复习推送（创新点） |

#### learning_records — 学习记录表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| student_id | VARCHAR(36) FK | 关联学生 |
| resource_id | INTEGER FK | 关联资源 |
| action | VARCHAR(30) | view / complete / answer / ask |
| topic | VARCHAR(100) | 相关知识点 |
| score | REAL | 答题得分 0-1 |
| time_spent | INTEGER | 花费时间（秒） |

---

## 6. API 接口设计

### 6.1 接口总览

| 方法 | 路径 | 用途 | 响应方式 |
|------|------|------|----------|
| `GET` | `/` | 健康检查 | JSON |
| `POST` | `/api/profile/chat` | 对话式画像构建 | **SSE 流式** |
| `GET` | `/api/profile/{student_id}` | 获取学生画像 | JSON |
| `PUT` | `/api/profile/{student_id}` | 更新画像 | JSON |
| `POST` | `/api/planner/generate` | 生成学习路径 | **SSE 流式** |
| `GET` | `/api/planner/{student_id}` | 获取学习路径 | JSON |
| `POST` | `/api/resource/generate` | 生成学习资源 | 异步任务（返回 task_id） |
| `GET` | `/api/resource/{resource_id}` | 获取资源详情 | JSON |
| `GET` | `/api/resource/list` | 资源列表 | JSON |
| `POST` | `/api/tutor/chat` | 智能辅导问答 | **SSE 流式** |
| `POST` | `/api/evaluate/start` | 开始学习评估 | JSON |
| `GET` | `/api/evaluate/report/{student_id}` | 获取评估报告 | JSON |
| `POST` | `/api/evaluate/record` | 提交学习记录 | JSON |
| `GET` | `/api/task/{task_id}/status` | 查询异步任务进度 | JSON |

### 6.2 统一规范

- 所有接口前缀 `/api/`
- 流式接口统一 SSE，`Content-Type: text/event-stream`
- 异步任务返回 `task_id`，前端轮询 `/api/task/{id}/status`
- 错误响应统一格式：`{"error": true, "code": "ERROR_CODE", "message": "描述"}`
- 学生 ID 使用 UUID

### 6.3 核心接口示例

#### 画像对话（SSE 流式）

```
POST /api/profile/chat

请求：
{
  "student_id": "stu_001",
  "message": "我是大二学生，在学机器学习，数学基础不太好..."
}

响应（SSE 流式）：
data: {"type":"chat","content":"了解了，你的数学基础..."}
...
data: {"type":"profile_update","profile":{...6个维度...}}
data: {"type":"done"}
```

#### 资源生成（异步任务）

```
POST /api/resource/generate
→ {"task_id":"task_abc","status":"pending"}

GET /api/task/task_abc/status
→ {"status":"generating","progress":0.6,"message":"正在生成练习题..."}

GET /api/task/task_abc/status
→ {"status":"done","result":{"resources":[...]}}
```

---

## 7. Agent 设计

### 7.1 Agent 协同流程（LangGraph）

```
用户对话
    │
    ▼
ProfileAgent ── 构建/更新学生画像（6 维 + 遗忘曲线数据）
    │
    ├──────────┐
    ▼          ▼
PlannerAgent  ResourceAgent  ← 并行执行
生成路径      生成资源
    │          │
    └────┬─────┘
         ▼
    推送到前端
         │
    ┌────┴────┐
    ▼         ▼
TutorAgent  EvaluateAgent  ← 用户主动触发
即时问答     学习评估
               │
               ▼
         评估 → 调整路径/资源 → 闭环
```

![时序图](images/sequence.png)

*图 7-1：多 Agent 协同工作时序图。展示了学生用户从发起对话到获得学习资源的完整交互过程：(1) 学生在 ProfilePage 输入学习描述 → ProfileAgent 通过 LLM 分析并返回学生画像；(2) 画像就绪后 PlannerAgent 和 ResourceAgent 并行执行——前者生成学习路径，后者生成配套学习资源；(3) 结果推送到前端，学生可在 TutorPage 发起智能问答，或在 EvaluatePage 查看学习评估报告。整个过程采用 SSE 流式传输，保证交互的实时性。*

### 7.2 Agent 职责与输入/输出

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **ProfileAgent** | 对话式构建画像 | message, history, current_profile | chat_reply + profile(6维) |
| **PlannerAgent** | 生成学习路径 | profile, goal | goal + stages[] |
| **ResourceAgent** | 生成学习资源 | topic, types[], difficulty, profile | resources[] |
| **TutorAgent** | 智能辅导问答 | question, context, explanation_style | chat_response + diagrams + references |
| **EvaluateAgent** | 学习效果评估 | student_id, profile, records, path | overall_score + dimensions + suggestions |

### 7.3 防幻觉机制

在每个 Agent 的 System Prompt 中嵌入以下约束：

```
你是一个学术类 AI 助手，请遵守：
1. 只回答你确定的内容，不确定请标注"建议核实"
2. 公式、定理、年份等务必核实准确性
3. 超出知识范围请诚实告知
4. 不生成违规、敏感或不安全的内容
```

RAG 增强：生成内容附带"参考来源"，提升内容可信度。

---

## 8. 创新点设计

### 8.1 遗忘曲线驱动间隔复习

**核心算法**：
- 艾宾浩斯遗忘曲线公式：R = e^(-t/S)
  - R：记忆保留率
  - t：距上次学习的时间
  - S：相对记忆强度（随正确复习增加，错误减少）
- 每次学生学习/答题 → 记录时间戳 + 正确率 → 更新 S
- 当 R 降至阈值（0.6）以下 → 自动推送复习内容
- 存储于 `student_profiles.memory_strength` 字段

### 8.2 多解释路径生成

TutorAgent 支持 4 种解释风格切换：
- 类比法（analogy）：日常生活类比
- 公式法（formula）：数学公式推导
- 图示法（visual）：Mermaid 流程图可视化
- 故事法（story）：小故事串联知识点

实现方式：Prompt Engineering，在 System Prompt 中预设 4 种风格模板。

---

## 9. 内容安全设计

### 9.1 双重过滤机制

```
输入 → 关键词过滤 → LLM 生成 → Prompt 约束 → 输出过滤 → 返回
```

- **关键词过滤**：敏感词库匹配 → 拦截
- **Prompt 约束**：System Prompt 中限定安全边界
- **输出校验**：检查生成内容是否包含违规信息

### 9.2 敏感词库

维护一个基础敏感词列表，在 `content_filter.py` 中实现：
- 政治敏感词过滤
- 暴力/色情内容过滤
- 学术不端行为过滤（如代写论文请求）

---

## 10. 部署方案

### 10.1 Docker Compose

```yaml
services:
  frontend:    # React build + Nginx
  backend:     # FastAPI + uvicorn
  chromadb:    # 向量数据库（可选独立部署）
  # MySQL 和 Redis 按需添加
```

### 10.2 评委启动方式

```bash
# 一键启动
docker-compose up -d

# 访问
前端：http://localhost:3000
后端 API 文档：http://localhost:8000/docs
```

### 10.3 降级方案

如果 Docker 有问题，提供手动启动脚本：
- `start.sh`（Linux/Mac）
- `start.bat`（Windows）

---

## 11. 开源合规

| 依赖 | 协议 |
|------|------|
| FastAPI | MIT |
| LangChain / LangGraph | MIT |
| ChromaDB | Apache 2.0 |
| React / Vite | MIT |
| Ant Design | MIT |
| Vercel AI SDK | Apache 2.0 |
| sentence-transformers | Apache 2.0 |
| SQLAlchemy | MIT |
| python-pptx | MIT |
| Mermaid | MIT |
| markmap | MIT |

> 所有依赖均为 MIT 或 Apache 2.0 协议，可自由使用。详见 README.md 开源致谢部分。
