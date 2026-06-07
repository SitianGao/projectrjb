# 24天完整作战计划 — 从零到交付

> **赛题**：第15届软件杯 A3 — 基于大模型的个性化学习资源生成与学习多智能体系统
> **约束**：24天 | 3人 | 期末第18-22天 | 全部功能需求必须满足
> **核心策略**：前17天完成所有开发，第18-22天安心考试，第23-24天最终收尾

---

## 第一部分：新手必读 —— 五层架构

### 1.1 五层架构并行开发

```
┌────────────────────────────────────────────┐
│  部署层 (Docker/Nginx)         ← Day 16+    │
├────────────────────────────────────────────┤
│  前端层 (React + Ant Design)   ← Day 3 开始 │
├────────────────────────────────────────────┤
│  后端层 (FastAPI)              ← Day 1 开始 │
├────────────────────────────────────────────┤
│  AI 层 (Agent + LLM + RAG)     ← Day 1 开始 │
├────────────────────────────────────────────┤
│  数据层 (SQLite + ChromaDB)    ← Day 2 建表 │
└────────────────────────────────────────────┘
```

**核心原则**：前端和后端可以并行开发（前端先用 Mock 数据）。Agent 层和后端可以同时开发（Agent 是纯 Python 函数）。

---

## 第二部分：压缩版 24 天时间线

> ⚠️ **期末考试在第 18-22 天，完全不安排开发任务。所有代码必须在 Day 17 之前完成。**

### 总览

```
              Week 1 (开发)     │      Week 2 (开发)       │    Week 3 (冲刺)      │  Week 4
D1-2    D3-4    D5-6    D7    │ D8-9    D10-11  D12     │ D13-15   D16-17      │ D18-22   D23-24
──────────────────────────────┼──────────────────────────┼───────────────────────┼──────────────
环境搭建  Agent    Agent  前后端│ 功能    创新点   安全    │ 联调     修bug       │ 🔴期末   最终收尾
LLM验证  核心逻辑  API开发 对接  │ 补全    实现     过滤    │ 测试     部署准备    │ 考试     文档+演示
建表     前端框架  前端页面     │ RAG     异步     体验   │ 性能     验收        │         打包提交
分工确认  知识数据             │ 完整    任务     打磨   │ 优化     清单        │
──────────────────────────────┼──────────────────────────┼───────────────────────┼──────────────
▼                             │ ▼                        │ ▼                     │ ▼
✅ LLM调通                    │ ✅ 完整流程跑通           │ ✅ 所有需求打勾        │ ✅ 作品提交
✅ 3人能Push                   │ ✅ 前端不用Mock           │ ✅ 性能达标            │ ✅ 答辩就绪
```

### 每日任务表

| 阶段 | 天数 | 队长（后端+Agent） | 队员A（前端） | 队员B（RAG+知识库） |
|------|------|-------------------|-------------|-------------------|
| 环境搭建 | Day 1-2 | FastAPI 骨架 + LLM 验证 | React 骨架 + Ant Design | 知识数据收集 + SQLite 建表 |
| 核心开发 | Day 3-6 | 5 个 Agent + Orchestrator + API | 6 个页面 + 组件 + Mock 数据 | RAG 管线 + 安全过滤 + Agent 逻辑 |
| 前后端对接 | Day 7-9 | Agent → API 包装 + 流式输出 | Mock → 真实 API + SSE 对接 | 知识库完善 + 检索调优 |
| 功能补全 | Day 10-12 | 创新点实现 + 异步任务 | 体验打磨 + 动效 + 错误处理 | 题库补充 + 安全测试 |
| 联调测试 | Day 13-15 | 端到端联调 + 性能优化 | 响应式适配 + 极端情况处理 | 测试用例 + 内容安全验证 |
| Bug修复 | Day 16-17 | 修 bug + Docker 配置 | Bug 修复 + 最终 UI 调整 | 文档初稿 + 开源标注 |
| 🔴期末 | Day 18-22 | 不开发，只复习考试 | 不开发，只复习考试 | 不开发，只复习考试 |
| 收尾 | Day 23-24 | 最终打包 + 演示脚本 | 演示视频录制 | 文档完善 + 提交检查 |

---

## 第三部分：创新点

> 以下是**超出赛题要求的真正创新点**。

### 推荐方案：遗忘曲线驱动间隔复习 + 多解释路径生成

**① 遗忘曲线驱动复习**
- 核心：利用艾宾浩斯遗忘曲线（R = e^(-t/S)），知识点即将遗忘时自动推送复习
- 实现：约 50 行 Python
- 答辩价值：将认知科学的遗忘曲线理论引入智能学习系统

**② 多解释路径生成**
- 核心：学生对概念不理解时，用 4 种方式（类比法、公式法、图示法、故事法）分别解释
- 实现：纯 Prompt Engineering，零额外成本
- 答辩价值：提出"多视角解释生成机制"

---

## 第四部分：技术选型（完整）

| 层面 | 选择 | 理由 |
|------|------|------|
| **大模型** | 讯飞星火 Spark 4.0（主）+ DeepSeek（备） | 赛题方是讯飞；DeepSeek 备份 |
| **后端** | FastAPI + LangGraph | 原生异步、SSE 流式、Agent 编排 |
| **前端** | React 19 + Vite + Ant Design 5 + Vercel AI SDK | 组件丰富、流式内置 |
| **数据库** | SQLite（开发）→ MySQL（提交） | 零配置开发，提交切 MySQL |
| **向量库** | ChromaDB | pip install 即用 |
| **嵌入模型** | sentence-transformers | 本地运行，不消耗 API |
| **思维导图** | markmap | Markdown 秒变思维导图 |
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

---

## 第五部分：项目目录结构

```
projectrjb/
├── README.md
├── .gitignore
├── docs/                        # 文档
├── backend/                     # 后端（队长）
│   ├── app.py
│   ├── config.py
│   ├── api/          (7 个路由)
│   ├── agents/       (编排 + 基类 + LLM客户端)
│   ├── models/       (5 张表 ORM)
│   ├── services/     (6 个服务)
│   └── utils/        (日志 + 任务管理)
├── frontend/                    # 前端（队员A）
│   └── src/
│       ├── api/       (6 个封装)
│       ├── pages/     (6 个页面)
│       ├── components/(10 个组件)
│       └── hooks/     (2 个 Hook)
├── data/                        # 数据（队员B）
│   ├── knowledge/    (知识库)
│   └── sql/          (建表脚本)
└── test/                        # 测试（队员B）
```

---

## 第六部分：API 接口总览

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

---

## 第七部分：数据库表（5 张）

| 表名 | 用途 | 核心字段 |
|------|------|----------|
| `students` | 学生基础信息 | id(UUID), nickname |
| `student_profiles` | 学生画像（含遗忘曲线） | 6 维度 + memory_strength |
| `learning_paths` | 学习路径 | goal, stages(JSON), current_stage |
| `resources` | 学习资源 | type, title, content, topic, difficulty |
| `learning_records` | 学习记录 | action, topic, score, time_spent |

---

## 第八部分：Agent 协同流程

```
用户对话 → ProfileAgent（画像）
                │
        ┌───────┴───────┐
        ▼               ▼
  PlannerAgent    ResourceAgent   ← 并行！
  （路径）         （资源）
        │               │
        └───────┬───────┘
                ▼
        推送前端 → TutorAgent/EvaluateAgent（按需触发）
                                         │
                                   评估 → 调整路径 → 闭环
```

---

## 第九部分：验收清单

### 功能性需求
- [ ] 对话式学生画像构建（6 个维度 + 动态更新）
- [ ] 多 Agent 协同资源生成（5+ 类资源）
- [ ] 个性化学习路径规划（含阶段目标）
- [ ] 基于路径的资源推送
- [ ] 智能辅导问答（文本 + 图解）
- [ ] 学习效果评估（进度 + 掌握度 + 效率）
- [ ] 评估→调整→闭环

### 非功能性需求
- [ ] 流式输出 | Markdown 渲染 | 多模态卡片展示
- [ ] 内容安全过滤 | 防幻觉机制 | 开源标注

### 性能需求
- [ ] 对话 ≤ 5 秒 | 生成有进度提示
- [ ] Agent 无依赖并行 | LLM 失败重试
- [ ] 异常有错误提示

### 创新点
- [ ] 遗忘曲线复习 或 多解释路径
- [ ] 文档中论证科学问题

---

## 第十部分：风险管理

| 风险 | 应对 |
|------|------|
| 星火 API 不稳定 | DeepSeek 自动切换 |
| LLM JSON 格式不稳定 | Prompt 锁死 + try-except + 重试 |
| ChromaDB 搞不定 | 降级：JSON + sklearn 余弦相似度 |
| 代码合并不起来 | 队长负责集成，PR 审批 |
| 前 5 天都在搭环境 | Day 1 必须跑通 LLM API |
| 期末考试压缩时间 | 前 17 天高强度，每天多投入 2-3h |

---

## 第十一部分：GitHub 协作规范

参见 `docs/github-workflow.md`

**三个分支**：
- `feature/backend-core` — 队长
- `feature/frontend-core` — 队员A
- `feature/ai-core` — 队员B

**每日操作**：
1. `git checkout main && git pull`
2. `git checkout 自己的分支 && git merge main`
3. 写代码 → commit → push
4. 功能完成 → 创建 PR → 队长 Review → Merge

---

## 总结

```
D1-2 ─── D3-6 ─── D7-9 ─── D10-12 ─── D13-15 ─── D16-17 ─── D18-22 ─── D23-24
环境    核心开发  前后端    功能补全   联调测试    Bug修复    🔴期末考试  最终收尾
         ████████████████████████████████████████████              ██
         所有开发压缩在前17天                                       考后冲刺
```
