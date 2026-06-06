# GitHub 协作规范 —— 三人开发流程

> **本文档是 3 个人的操作手册。** 严格按照这个流程走，避免代码冲突和集成灾难。

---

## 一、分支架构

```
main ──────────────────────────────────────────────→ (只放稳定代码)
  │
  ├── feature/backend-core     (队长：后端 + Agent + API)
  ├── feature/frontend-core    (队员A：前端全部)
  └── feature/ai-core          (队员B：RAG + 知识库 + 安全)
```

---

## 二、每个人要创建的分支和文件清单

### 🔧 队长 — feature/backend-core

```
你负责的分支：feature/backend-core

你需要创建的文件：
──────────────────────────────────────────────────

backend/
├── requirements.txt            # Python 依赖列表
├── app.py                      # FastAPI 入口，注册所有路由
├── config.py                   # 配置（数据库URL、API Key等）

backend/api/                     # API 路由层
├── __init__.py
├── profile_api.py              # POST /api/profile/chat, GET /api/profile/{id}
├── planner_api.py              # POST /api/planner/generate, GET /api/planner/{id}
├── resource_api.py             # POST /api/resource/generate, GET /api/resource/{id}
├── tutor_api.py                # POST /api/tutor/chat
├── evaluate_api.py             # POST /api/evaluate/start, GET /api/evaluate/report/{id}
└── task_api.py                 # GET /api/task/{id}/status

backend/agents/                  # Agent 编排层
├── __init__.py
├── base_agent.py               # Agent 基类（流式调用 + 重试 + 日志）
├── llm_client.py               # LLM 统一封装（星火 + DeepSeek 切换）
└── orchestrator.py             # Agent 编排器（LangGraph 状态图）

backend/models/                  # 数据库模型（SQLAlchemy ORM）
├── __init__.py
├── student.py
├── learning_path.py
├── resource.py
└── evaluation.py

backend/services/                # 业务逻辑层
├── __init__.py
├── profile_service.py
├── planner_service.py
├── resource_service.py
├── tutor_service.py
└── evaluate_service.py

backend/utils/
├── __init__.py
├── logger.py
└── task_manager.py             # 异步任务管理
```

**创建分支命令**（在 VSCode 终端中执行）：
```bash
git checkout main
git pull origin main
git checkout -b feature/backend-core
# 然后创建上述文件...
```

---

### 🎨 队员A — feature/frontend-core

```
你负责的分支：feature/frontend-core

你需要创建的文件：
──────────────────────────────────────────────────

frontend/
├── package.json                # 用 npm create vite@latest 生成
├── vite.config.js
├── index.html

frontend/src/
├── main.jsx                    # React 入口
├── App.jsx                     # 根组件 + 路由配置
├── App.css

frontend/src/api/               # 后端 API 调用封装
├── client.js                   # axios 实例 + 基础配置（baseURL, 错误处理）
├── profile.js                  # 画像相关 API 函数
├── planner.js                  # 规划相关 API 函数
├── resource.js                 # 资源相关 API 函数
├── tutor.js                    # 辅导相关 API 函数
└── evaluate.js                 # 评估相关 API 函数

frontend/src/pages/             # 页面组件（每个路由对应一个）
├── HomePage.jsx                # 首页/仪表盘
├── ProfilePage.jsx             # 学生画像页（对话 + 画像卡片）
├── LearningPathPage.jsx        # 学习路径页（时间线/步骤条）
├── ResourcePage.jsx            # 学习资源页（资源卡片列表）
├── TutorPage.jsx               # 智能辅导页（问答聊天界面）
└── EvaluatePage.jsx            # 学习评估页（进度 + 评分图表）

frontend/src/components/        # 可复用组件
├── ChatBox.jsx                 # 通用对话组件（输入框 + 消息列表 + 流式显示）
├── ProfileCard.jsx             # 画像卡片组件
├── ResourceCard.jsx            # 资源卡片组件（文档/题目/思维导图）
├── PathTimeline.jsx            # 学习路径时间线组件
├── MindMapViewer.jsx           # 思维导图查看器（封装 markmap）
├── MermaidChart.jsx            # 图表渲染器（封装 mermaid）
├── MarkdownRenderer.jsx        # Markdown 渲染器（封装 react-markdown）
├── QuizCard.jsx                # 练习题卡片组件
├── ProgressBar.jsx             # 生成进度条组件
└── LoadingSkeleton.jsx         # 加载骨架屏

frontend/src/hooks/
├── useChat.js                  # 对话 hook（封装 Vercel AI SDK 的 useChat）
└── useTaskStatus.js            # 异步任务轮询 hook

frontend/src/utils/
└── format.js                   # 日期/文本格式化工具
```

**创建分支命令**：
```bash
git checkout main
git pull origin main
git checkout -b feature/frontend-core
# 用 Vite 创建项目：npm create vite@latest frontend -- --template react
# 然后安装依赖：cd frontend && npm install
# 然后创建上述文件结构...
```

---

### 🧠 队员B — feature/ai-core

```
你负责的分支：feature/ai-core

你需要创建的文件：
──────────────────────────────────────────────────

backend/agents/                  # Agent 核心逻辑（和队长协作）
├── profile_agent.py            # 学生画像 Agent（对话 → 画像提取）
├── planner_agent.py            # 学习规划 Agent（画像 → 路径）
├── resource_agent.py           # 资源生成 Agent（主题 → 资源）
├── tutor_agent.py              # 智能辅导 Agent（问题 → 答案）
└── evaluate_agent.py           # 学习评估 Agent（记录 → 评估报告）

backend/rag/                     # RAG 检索管线
├── __init__.py
├── embedding.py                # 文本转向量（sentence-transformers）
├── vector_store.py             # ChromaDB 操作封装（增删查）
├── retriever.py                # 检索逻辑（查询 → 相关文档）
└── knowledge_loader.py         # 知识数据导入脚本

backend/safety/                  # 内容安全
├── __init__.py
└── content_filter.py           # 敏感词过滤 + Prompt 安全约束

data/
├── knowledge/                   # 知识库原始数据
│   ├── ml_basics.md            # 机器学习基础知识点
│   ├── ml_advanced.md          # 机器学习进阶
│   ├── dl_basics.md            # 深度学习基础
│   └── exercises.json          # 题库（JSON 格式）
│
└── sql/                         # 数据库脚本
    ├── schema.sql              # 建表语句（5 张表）
    └── seed.sql                # 初始测试数据（可选）

test/                            # 测试文件
├── test_profile_agent.py
├── test_planner_agent.py
├── test_resource_agent.py
├── test_rag.py
└── test_safety.py
```

**创建分支命令**：
```bash
git checkout main
git pull origin main
git checkout -b feature/ai-core
# 然后创建上述文件...
```

---

## 三、每日操作流程

### 每个人早上开始写代码前（3 步，2 分钟）：

```
Step 1：切换到 main 并拉取最新代码
        VSCode 左下角点分支名 → 选 "main"
        点 🔄 同步按钮

Step 2：切回自己的开发分支
        VSCode 左下角点分支名 → 选你自己的分支
        (队长: feature/backend-core)
        (队员A: feature/frontend-core)
        (队员B: feature/ai-core)

Step 3：把 main 的最新代码合并到自己分支
        VSCode 终端执行：
        git merge main
        → 如果没有冲突，直接继续
        → 如果有冲突，按第六部分解决
```

### 写完代码后提交（VSCode 图形界面）：

```
1. 左侧栏点 🝆 源代码管理图标
2. 在 "Message" 输入框写 commit 说明
   格式：feat: 做了什么 / fix: 修了什么
3. 点 ✓ 提交
4. 点 🔄 同步更改（Push）
```

### Commit 信息规范：

```
✅ 正确：
feat: 完成ProfileAgent流式对话功能
fix: 修复SSE连接超时问题
refactor: 重构LLMClient的错误处理
docs: 更新API接口文档

❌ 错误：
update
修bug
111
.
```

---

## 四、Pull Request 流程

### 队员操作（提交 PR）：

```
1. 确认自己分支的代码已 push 到 GitHub
2. 打开 GitHub 网页 → 进入仓库 projectrjb
3. 点 "Pull requests" 标签 → "New pull request"
4. base: main ← compare: 你的分支名
5. 标题写清楚改了什么
   例："feat: 完成学习路径页面和时间线组件"
6. 描述里写：
   - 新增了什么功能
   - 改了哪些文件
   - 有没有截图（前端必带截图）
   - 有没有需要队长注意的地方
7. 点 "Create pull request"
8. 在微信群里 @队长 "PR 已提交，请 Review"
```

### 队长操作（Review + Merge）：

```
1. GitHub → Pull requests → 点开 PR
2. 点 "Files changed" 查看改动
3. 逐文件检查：
   - 代码逻辑对吗？
   - 有没有明显的 bug？
   - 格式符合规范吗？
   - 有没有和别人的代码冲突的迹象？
4. 有两种结果：

   通过 ✅：
   - 点 "Review changes" → 选 "Approve"
   - 点 "Merge pull request" → "Confirm merge"
   - 微信群通知所有人："main 已更新，大家 git merge main 到自己分支"

   需要修改 ❌：
   - 在具体代码行旁边点 ➕，写评论
   - 点 "Review changes" → 选 "Request changes"
   - 队员看到评论 → 修改 → push → PR 自动更新 → 你再 Review
```

---

## 五、队长处理分支的标准流程（一步步）

### 每天早上（5 分钟）：

```
1. 打开 GitHub 仓库 → Pull requests 标签
2. 检查有没有新的 PR
   → 有 → Review（按上面的流程）
   → 没有 → 继续往下

3. 打开 Insights → Network 查看提交图
   → 确认每个人都提交了
   → 如果某人昨天没提交 → 私聊问情况

4. 合并完所有 PR 后，在微信群发：
   "@所有人 main 已更新，大家 git merge main 到自己分支后再开始写代码"
```

### 每天晚上（3 分钟）：

```
1. 检查 GitHub Project 看板
   → 更新任务卡片状态
   → "进行中" 的卡片超过 3 天没动 → 明天重点关注

2. 在微信群发第二天的任务提醒：
   "明天各自的任务：@队员A 完成 ResourcePage，@队员B 完成 knowledge_loader"
```

### 遇到冲突时：

```
如果队员的 PR 显示 "Can't automatically merge"：

你的操作：
1. 不要强行 merge！
2. 在 PR 页面评论区 @队员："你的分支和 main 有冲突，请先解决冲突"
3. 队员操作：
   git checkout main
   git pull origin main
   git checkout 自己的分支
   git merge main
   → VSCode 会显示冲突文件
   → 解决冲突（见第六部分）
   → git add . → git commit → git push
4. PR 会自动更新，冲突消失
5. 你再 Review + Merge
```

### 当你自己要合并代码时：

```
你自己的 feature/backend-core → main 的流程：

1. 确保你的分支代码已全部 push
2. 切到 main：git checkout main
3. 拉最新：git pull origin main
4. 合并你的分支：git merge feature/backend-core
5. 如果有冲突 → 解决 → commit
6. 推送到 GitHub：git push origin main
7. 切回开发分支：git checkout feature/backend-core
8. 更新开发分支：git merge main
```

---

## 六、冲突解决（VSCode 图形界面）

### 冲突长什么样：

```
<<<<<<< Current Change (你的版本)
learning_goal = "掌握机器学习"
=======
learning_goal = "掌握深度学习基础算法"
>>>>>>> Incoming Change (别人的版本)
```

### 解决步骤：

```
1. VSCode 会在冲突文件旁边标红色 ⚠️
2. 点开文件，看到冲突标记
3. 每个冲突有 3 个按钮：
   [Accept Current]  → 保留你的版本
   [Accept Incoming] → 用队友的版本
   [Accept Both]     → 两个都保留
4. 或者手动编辑成你想要的内容
5. 所有冲突解决后 → 保存文件
6. VSCode 左侧 🝆 → 输入 "fix: 解决合并冲突"
7. ✓ Commit → 🔄 Sync
```

### 减少冲突的 3 条铁律：

1. **每人只改自己负责的文件**。队员A 不动 backend/，队长不动 frontend/，队员B 不动别人负责的文件
2. **每天早上先 merge main 到自己的分支**（见第三节 Step 3）
3. **小步提交**。写完一个小功能就 commit，别攒 3 天一起

---

## 七、常见问题

| 问题 | 解决办法 |
|------|----------|
| push 被拒绝 `! [rejected]` | 先 `git pull origin main` 再 `git push` |
| 不小心改错了文件想撤销 | VSCode 源代码管理 → 右键文件 → Discard Changes |
| commit 信息写错了 | 终端：`git commit --amend -m "新信息"` |
| 不知道自己在哪个分支 | VSCode 左下角查看，或终端 `git branch` |
| 代码完全乱了想重来 | 关 VSCode → 删本地文件夹 → 重新 clone |
| 合并时大面积冲突（>5 个文件） | 不要自己解决，叫涉及冲突的队员一起看 |

---

## 八、分工边界（最重要的一条）

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   队长负责的文件：backend/ 下所有文件（除 agents/ 中     │
│   标注队员B 负责的 5 个 Agent 文件）                      │
│                                                         │
│   队员A 负责的文件：frontend/ 下所有文件                  │
│                                                         │
│   队员B 负责的文件：                                     │
│   ├── backend/agents/profile_agent.py                   │
│   ├── backend/agents/planner_agent.py                   │
│   ├── backend/agents/resource_agent.py                  │
│   ├── backend/agents/tutor_agent.py                     │
│   ├── backend/agents/evaluate_agent.py                  │
│   ├── backend/rag/ 下所有文件                           │
│   ├── backend/safety/ 下所有文件                        │
│   ├── data/ 下所有文件                                  │
│   └── test/ 下所有文件                                  │
│                                                         │
│   ⚠️ 不要越界改别人的文件！                              │
│   如果必须改别人的文件，先在群里问。                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 九、快速参考卡片

```
┌──────────────────────────────────────────────────────────┐
│                    每日操作清单                            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  早上（每个人）：                                          │
│  1. git checkout main && git pull                        │
│  2. git checkout 自己的分支                               │
│  3. git merge main                                       │
│  4. 开始写代码                                            │
│                                                          │
│  写完代码后（每个人）：                                     │
│  1. git add .                                            │
│  2. git commit -m "feat: xxx"                            │
│  3. git push                                             │
│  4. 功能完成时 → 去 GitHub 创建 PR                         │
│                                                          │
│  队长额外（每天早晚）：                                     │
│  早上：检查 PR → Review → Merge → 通知全队                 │
│  晚上：更新看板 → 发次日任务                               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```
