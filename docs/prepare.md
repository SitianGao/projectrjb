# EduAgent 项目启动准备指南

> **赛题**：第15届软件杯 A3 — 基于大模型的个性化学习资源生成与学习多智能体系统
> **时间**：约 24 天 | **团队**：3 人 | **状态**：准备期

---

## 1. 团队分工

| 角色 | 负责内容 | 核心交付物 |
|------|----------|-----------|
| **队长（你）** | 后端 API + Agent 编排 + 集成 + 项目进度 | FastAPI 全部端点、AgentOrchestrator、LLM 调用封装、最终集成 |
| **队员A** | 前端全部 | React 页面、流式展示、Markdown 渲染、多模态卡片、所有交互 |
| **队员B** | AI 层 + RAG + 知识库 + 安全 | Agent 核心逻辑、ChromaDB 搭建、知识数据整理、内容安全过滤 |

---

## 2. 技术选型

| 层面 | 选择 | 理由 |
|------|------|------|
| **大模型** | 讯飞星火 Spark 4.0（主）+ DeepSeek（备） | 赛题方是讯飞，使用星火有加分；DeepSeek 作为备份 |
| **后端框架** | FastAPI + LangGraph | 原生异步、SSE 流式、Swagger 自动文档；LangGraph 做 Agent 编排 |
| **前端框架** | React 19 + Vite + Ant Design 5 + Vercel AI SDK | 组件丰富、AI SDK 内置流式支持 |
| **数据库** | SQLite（开发）→ MySQL（提交） | 零配置开发，提交时切换显专业 |
| **向量库** | ChromaDB | 最轻量，pip install 即用 |
| **嵌入模型** | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) | 本地运行，不消耗 API |
| **RAG** | LangChain | 与 Agent 框架统一生态 |
| **思维导图** | markmap | Markdown 列表自动渲染为思维导图 |
| **PPT** | python-pptx | 简单 PPT 生成 |
| **部署** | Docker Compose | 评委一键启动 |

### Python 依赖

```txt
fastapi==0.115.*
uvicorn[standard]==0.34.*
sse-starlette==2.*
langchain==0.3.*
langgraph==0.2.*
langchain-community==0.3.*
chromadb==0.5.*
sentence-transformers==3.*
sqlalchemy==2.*
aiosqlite==0.20.*
python-pptx==1.*
python-multipart==0.0.*
httpx==0.28.*
pydantic==2.*
```

### JavaScript 依赖

```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "antd": "^5.22.0",
    "@ant-design/icons": "^5.5.0",
    "ai": "^4.0.0",
    "@ai-sdk/openai": "^1.0.0",
    "react-markdown": "^9.0.0",
    "react-syntax-highlighter": "^15.6.0",
    "markmap-lib": "^0.18.0",
    "mermaid": "^11.0.0",
    "axios": "^1.7.0"
  }
}
```

---

## 3. 创新点

> ⚠️ 以下是**超出赛题要求的真正创新点**，不是赛题内置的功能需求。

### 推荐方案：遗忘曲线驱动间隔复习 + 多解释路径生成

**① 遗忘曲线驱动复习**
- 核心：利用艾宾浩斯遗忘曲线模型（R = e^(-t/S)），在学生对知识点即将遗忘时自动推送复习内容
- 实现：约 50 行 Python，记录学习时间戳 + 正确率 → 计算记忆强度 → 低于阈值触发复习
- 答辩价值：将认知科学的遗忘曲线理论引入智能学习系统

**② 多解释路径生成**
- 核心：学生对同一概念不理解时，系统用 4 种方式分别解释（类比法、公式法、图示法、故事法）
- 实现：纯 Prompt Engineering，在 TutorAgent 的 System Prompt 中定义 4 种解释风格
- 答辩价值：提出"多视角解释生成机制"解决"因材施教"问题

> 两个创新点都不需要自研模型、不需要大数据、不需要复杂数学，但答辩时很好讲。

---

## 4. 项目目录结构

```
projectrjb/
├── README.md
├── .gitignore
├── docker-compose.yml               # Day 18+
│
├── docs/                            # 📚 文档
│   ├── contestproblem.md
│   ├── requirement.md
│   ├── design.md
│   ├── test_plan.md
│   ├── 软件杯A3完整系统架构图.md
│   ├── prepare.md                   # 🆕 本文档
│   ├── github-workflow.md           # 🆕 GitHub 协作规范
│   ├── api-design.md                # 🆕 API 接口文档
│   └── innovation.md                # 🆕 创新点说明
│
├── backend/                         # 🔧 后端（队长负责）
│   ├── requirements.txt
│   ├── app.py                       # FastAPI 入口
│   ├── config.py                    # 配置文件
│   │
│   ├── api/                         # API 路由层
│   │   ├── profile_api.py
│   │   ├── planner_api.py
│   │   ├── resource_api.py
│   │   ├── tutor_api.py
│   │   ├── evaluate_api.py
│   │   └── task_api.py
│   │
│   ├── agents/                      # Agent 核心逻辑（队长 + 队员B）
│   │   ├── base_agent.py
│   │   ├── llm_client.py
│   │   ├── profile_agent.py
│   │   ├── planner_agent.py
│   │   ├── resource_agent.py
│   │   ├── tutor_agent.py
│   │   ├── evaluate_agent.py
│   │   └── orchestrator.py
│   │
│   ├── rag/                         # RAG 管线（队员B）
│   │   ├── embedding.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   └── knowledge_loader.py
│   │
│   ├── models/                      # 数据库模型（队长）
│   │   ├── student.py
│   │   ├── learning_path.py
│   │   ├── resource.py
│   │   └── evaluation.py
│   │
│   ├── services/                    # 业务逻辑层
│   ├── safety/                      # 内容安全（队员B）
│   │   └── content_filter.py
│   └── utils/
│
├── frontend/                        # 🎨 前端（队员A负责）
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/                     # API 调用封装
│       ├── pages/                   # 页面组件
│       │   ├── HomePage.jsx
│       │   ├── ProfilePage.jsx
│       │   ├── LearningPathPage.jsx
│       │   ├── ResourcePage.jsx
│       │   ├── TutorPage.jsx
│       │   └── EvaluatePage.jsx
│       ├── components/              # 可复用组件
│       │   ├── ChatBox.jsx
│       │   ├── ProfileCard.jsx
│       │   ├── ResourceCard.jsx
│       │   ├── PathTimeline.jsx
│       │   ├── MindMapViewer.jsx
│       │   ├── MermaidChart.jsx
│       │   ├── MarkdownRenderer.jsx
│       │   └── QuizCard.jsx
│       └── hooks/
│
├── data/                            # 💾 数据（队员B负责）
│   ├── knowledge/                   # 知识库原始数据
│   └── sql/                         # 建表语句
│       └── schema.sql
│
├── deploy/                          # 🚀 部署（Day 18+）
└── test/                            # 🧪 测试
```

---

## 5. 24 天时间线（压缩版）

> ⚠️ **期末考试在第 18-22 天，完全不开发。所有代码 Day 17 前完成。**

| 阶段 | 天数 | 队长（后端+Agent） | 队员A（前端） | 队员B（RAG+知识库） |
|------|------|-------------------|-------------|-------------------|
| 环境搭建 | Day 1-2 | FastAPI 骨架 + LLM 验证 | React 骨架 + Ant Design | 知识数据收集 + SQLite 建表 |
| 核心开发 | Day 3-6 | 5 个 Agent + Orchestrator + API | 6 个页面 + 组件 + Mock | RAG 管线 + 安全过滤 |
| 前后端对接 | Day 7-9 | Agent→API 包装 + 流式输出 | Mock→真实 API + SSE 对接 | 知识库完善 + 检索调优 |
| 功能补全 | Day 10-12 | 创新点实现 + 异步任务 | 体验打磨 + 动效 + 错误处理 | 题库补充 + 安全测试 |
| 联调测试 | Day 13-15 | 端到端联调 + 性能优化 | 响应式适配 | 测试用例 + 安全验证 |
| Bug修复 | Day 16-17 | 修 bug + Docker 配置 | Bug 修复 + UI 调整 | 文档初稿 + 开源标注 |
| 🔴期末 | Day 18-22 | **不开发，安心考试** | **不开发，安心考试** | **不开发，安心考试** |
| 收尾 | Day 23-24 | 最终打包 + 演示脚本 | 演示视频录制 | 文档完善 + 提交检查 |

---

## 6. API 接口总览

| 方法 | 路径 | 用途 | 响应 |
|------|------|------|------|
| `GET` | `/` | 健康检查 | JSON |
| `POST` | `/api/profile/chat` | 对话式画像构建 | SSE 流式 |
| `GET` | `/api/profile/{id}` | 获取学生画像 | JSON |
| `PUT` | `/api/profile/{id}` | 更新画像 | JSON |
| `POST` | `/api/planner/generate` | 生成学习路径 | SSE 流式 |
| `GET` | `/api/planner/{id}` | 获取学习路径 | JSON |
| `POST` | `/api/resource/generate` | 生成学习资源 | 异步任务 |
| `GET` | `/api/resource/{id}` | 获取资源详情 | JSON |
| `POST` | `/api/tutor/chat` | 智能辅导问答 | SSE 流式 |
| `POST` | `/api/evaluate/start` | 开始评估 | JSON |
| `GET` | `/api/evaluate/report/{id}` | 评估报告 | JSON |
| `GET` | `/api/task/{id}/status` | 异步任务进度 | JSON |

> 详细请求/响应格式见 `docs/api-design.md`

---

## 7. 数据库表（5 张）

| 表名 | 用途 | 核心字段 |
|------|------|----------|
| `students` | 学生基础信息 | id(UUID), nickname |
| `student_profiles` | 学生画像 | 6 个维度 + memory_strength (创新点) |
| `learning_paths` | 学习路径 | goal, stages(JSON), current_stage |
| `resources` | 学习资源 | type, title, content, topic, difficulty |
| `learning_records` | 学习记录 | action, topic, score, time_spent |

> 详细建表语句见 `data/sql/schema.sql`

---

## 8. Agent 协同流程

```
用户对话 → ProfileAgent（画像构建/更新）
                │
        ┌───────┴───────┐
        ▼               ▼
  PlannerAgent    ResourceAgent    ← 并行执行
  （学习路径）     （学习资源）
        │               │
        └───────┬───────┘
                ▼
        资源 + 路径推送前端
                │
        ┌───────┴───────┐
        ▼               ▼
  TutorAgent      EvaluateAgent    ← 用户主动触发
  （智能问答）     （学习评估）
                        │
                        ▼
                  评估 → 调整路径/资源 → 闭环
```

**关键优化**：PlannerAgent 和 ResourceAgent 并行执行（节省约 5 秒）

---

## 9. Prompt 工程要点

> 项目的核心质量取决于 LLM 输出质量，LLM 输出质量取决于 Prompt 质量。

**基本法则**：
1. **角色先行**：不写"请生成学习路径"，写"你是一个有10年经验的教育技术专家..."
2. **输出格式锁死**：必须严格按 JSON 格式返回，不要输出其他内容
3. **给例子（Few-shot）**：Prompt 中放 1-2 个示例，输出质量提升巨大
4. **设边界**：只回答 AI/机器学习相关的问题
5. **防幻觉**：不确定的内容标注"建议核实"

**防幻觉 Prompt 约束**（加在每个 Agent 的 System Prompt 中）：
```
你是一个学术类 AI 助手，请遵守：
1. 只回答你确定的内容，不确定请说明"建议进一步查阅资料"
2. 公式、定理、年份等务必核实准确性
3. 超出知识范围请诚实告知
4. 不生成违规、敏感或不安全的内容
```

---

## 10. 验收清单（对标赛题）

### 功能性需求
- [ ] 对话式学生画像构建，含 6 个维度
- [ ] 画像随学习过程动态更新
- [ ] 多 Agent 协同架构（至少 4 个 Agent）
- [ ] 生成 5+ 类学习资源
- [ ] 个性化学习路径规划（含阶段性目标）
- [ ] 基于路径的资源推送
- [ ] 智能问答/辅导（文本 + 图解）
- [ ] 学习效果评估（进度 + 掌握度 + 效率）
- [ ] 评估 → 调整路径 → 调整资源 闭环

### 非功能性需求
- [ ] 流式输出（Streaming）
- [ ] Markdown 渲染
- [ ] 多模态内容卡片化展示
- [ ] 内容安全过滤
- [ ] 防幻觉机制
- [ ] 开源标注

### 性能需求
- [ ] 对话 ≤ 5 秒（流式首字延迟 ≤ 2 秒）
- [ ] 多模态生成有进度提示
- [ ] 多 Agent 无依赖时并行处理
- [ ] LLM 调用有失败重试
- [ ] 异常情况有错误提示

### 创新点
- [ ] 遗忘曲线复习 或 多解释路径 实现
- [ ] 文档中论证解决了什么科学问题

---

## 11. 风险管理

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 星火 API 不稳定 | 中 | 致命 | DeepSeek 自动切换 |
| LLM 返回 JSON 格式不稳定 | 高 | 大 | Prompt 锁死格式 + try-except + 重试 |
| ChromaDB 搞不定 | 中 | 中 | 降级：JSON + sklearn 余弦相似度 |
| 三人的代码合并不起来 | 高 | 大 | 队长负责集成，PR 审批 |
| 某人进度严重落后 | 中 | 大 | Day 5 检查，调整分工 |
| 前 5 天都在搭环境 | 中 | 大 | Day 1 必须跑通 LLM API |

---

## 12. AI 编码工具使用策略

> 你们的核心优势：用 AI 工具弥补新手编码能力不足。

**给每个队员的规则**：
1. 一个功能拆成 3-5 个小步骤让 AI 写，不要一次性要求整个功能
2. AI 写的代码必须能看懂每一行在干什么
3. 跑不通就把报错贴回给 AI
4. 不确定 AI 的方案对不对 → 发群里讨论

**队长额外职责**：
- 队员遇到技术困难 → 你用 Claude Code 生成解决方案 → 发给队员
- 代码 Review 也可以用 AI："帮我审查这段代码的安全性和性能"

---

## 13. 参考文档

- `docs/contestproblem.md` — 赛题原文
- `docs/requirement.md` — 需求分析
- `docs/design.md` — 系统设计
- `docs/test_plan.md` — 测试计划
- `docs/github-workflow.md` — GitHub 协作规范（必读！）
