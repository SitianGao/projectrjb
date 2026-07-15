# ChatBox 到学习旅程一日联调任务清单

> 适用项目：EduAgent  
> 执行周期：1 天  
> 固定联调学生：`demo-student-01`  
> 接口依据：`docs/design.md` 第 6 章、第 10.4 节，以及 `docs/api.md`  
> 分工依据：`docs/design.md` 第 10.1 节、`docs/github-workflow.md` 第八节

---

## 1. 当天唯一目标

当天只打通以下主流程：

```text
画像对话
→ 画像完整度达到 0.85
→ 前端显示“开启学习之旅”
→ 用户确认后生成学习路径
→ 根据当前阶段生成学习资源
→ 轮询资源任务进度
→ 同页展示路径、资源和复习计划
→ 学习过程中使用 TutorAgent 辅导
→ 学习行为写入记录后刷新评估
```

当天不做：

- 不新增登录、权限或多用户系统。
- 不重构整个前端。
- 不增加新的业务 API 路径。
- 不新增自定义 SSE 事件类型。
- 不清理全部历史 lint。
- 不优化所有页面样式。
- 不一次性生成全部关卡资源，只保证当前关卡。
- 不修改已冻结的 Agent 核心字段名称。
- 15:00 后不接受非阻断功能。

---

## 2. 接口使用规范

本次联调只使用 `design.md` 已定义接口。

| 顺序 | 方法 | 接口 | 用途 | 负责人 |
|---:|---|---|---|---|
| 1 | `POST` | `/api/profile/chat` | 对话式构建画像，SSE | 队长 + A + B |
| 2 | `GET` | `/api/profile/{student_id}` | 刷新后恢复最新画像 | 队长 + A |
| 3 | `POST` | `/api/planner/generate` | 根据最新画像生成路径，SSE | 队长 + A + B |
| 4 | `GET` | `/api/planner/{student_id}` | 获取当前学习路径 | 队长 + A |
| 5 | `POST` | `/api/resource/generate` | 异步生成当前关卡资源 | 队长 + A + B |
| 6 | `GET` | `/api/task/{task_id}/status` | 轮询资源任务 | 队长 + A |
| 7 | `GET` | `/api/resource/list` | 获取学生已有资源 | 队长 + A |
| 8 | `GET` | `/api/resource/{resource_id}` | 查看资源详情 | 队长 + A |
| 9 | `POST` | `/api/tutor/chat` | 学习阶段智能辅导，SSE | 队长 + A + B |
| 10 | `POST` | `/api/evaluate/record` | 写入学习行为 | 队长 + A |
| 11 | `POST` | `/api/evaluate/start` | 生成或刷新评估 | 队长 + A + B |
| 12 | `GET` | `/api/evaluate/report/{student_id}` | 获取评分和复习计划 | 队长 + A |

### 2.1 不允许新增的接口或事件

本次不新增：

```text
/api/pipeline/start-journey
/api/journey/{student_id}
profile_ready
journey_ready
```

画像完成状态直接依据现有 ProfileAgent 输出：

```text
completeness >= 0.85
```

前端收到现有 `profile_update` 后，从返回对象中读取：

```text
student_id
profile
completeness
next_questions
```

每轮 SSE 仍按现有流程结束：

```text
start → chat → profile_update → done
```

### 2.2 通用响应规则

普通成功响应：

```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

普通失败响应：

```json
{
  "success": false,
  "error": true,
  "code": "ERROR_CODE",
  "message": "错误描述"
}
```

前端正式读取 `data` 内业务字段，不根据 Mock 猜测字段。

---

## 3. 队长任务清单

分支：`feature/backend-core`

负责范围：后端 API、Service、数据库、AgentOrchestrator、任务系统、接口契约、集成测试和封版。

禁止修改：

- `frontend/` 下文件。
- 队员 B 负责的五个 Agent 文件。
- `backend/rag/`、`backend/safety/`、`data/`、Agent 质量测试。

### 3.1 冻结接口和状态判断

- [ ] 在早会中确认本文件为当天任务基线。
- [ ] 确认所有人只调用第 2 节已有接口。
- [ ] 确认画像完成阈值为 `0.85`。
- [ ] 确认前端从 `profile_update` 读取 `completeness` 和 `next_questions`。
- [ ] 确认不新增 `profile_ready` 等临时事件。
- [ ] 确认 PlannerAgent、ResourceAgent、EvaluateAgent 输出字段不再变化。
- [ ] 将任何字段变更先同步到 `docs/api.md`，三人确认后才允许实现。

### 3.2 修复画像对话上下文

负责文件：

```text
backend/api/profile_api.py
backend/services/profile_service.py
backend/models/student.py（仅必要时）
```

任务：

- [ ] 当前端不传 `current_profile` 时，从数据库读取最新画像。
- [ ] 当前端不传 `history` 时，从最新画像记录的 `chat_history` 读取。
- [ ] 将数据库中的聊天历史转换成 ProfileAgent 接受的列表格式。
- [ ] 将已有画像传给 ProfileAgent 做增量更新。
- [ ] 保存新画像前读取旧 `completeness`。
- [ ] 最终保存值使用 `max(old_completeness, new_completeness)`，防止完整度回退。
- [ ] 每次画像更新继续保存新版本，但版本号必须连续递增。
- [ ] 避免同一轮 `profile_update` 被重复保存。
- [ ] `chat_history` 只记录成功完成的用户/助手消息。
- [ ] SSE 请求异常时返回统一 `PROFILE_CHAT_FAILED`，最后发送 `done`。
- [ ] 不在画像聊天接口中自动生成路径，必须等待用户点击确认。

验收：

```text
第 1 轮 completeness = 0.40
第 2 轮 completeness >= 0.40
第 3 轮 completeness >= 第 2 轮
刷新浏览器后继续聊天，画像和历史不丢失
```

### 3.3 保证路径生成使用最新画像

负责文件：

```text
backend/api/planner_api.py
backend/services/planner_service.py
backend/agents/orchestrator.py
```

任务：

- [ ] `/api/planner/generate` 根据 `student_id` 读取数据库最新画像。
- [ ] 未找到画像时返回 `PROFILE_NOT_FOUND`。
- [ ] 画像存在但信息不足时返回明确错误，不生成默认无关路径。
- [ ] 前端未传 `goal` 时，使用画像中的 `learning_goal`。
- [ ] 不再默认使用“掌握高中数学核心知识”。
- [ ] 路径生成成功后写入 `learning_paths`。
- [ ] 返回当前路径的 `id/path_id`，供资源生成关联。
- [ ] 路径必须包含 `goal`、`stages`、`current_stage`、`estimated_days`。
- [ ] 每个阶段必须包含 `stage_id`、`title`、`objectives`、`topics`、`tasks`。
- [ ] 重复点击生成时不允许创建并发重复请求。
- [ ] 保留旧路径版本，但 `GET /api/planner/{student_id}` 返回最新有效路径。

### 3.4 保证资源与路径正确关联

负责文件：

```text
backend/api/resource_api.py
backend/services/resource_service.py
backend/services/task_service.py
backend/utils/task_manager.py
backend/models/resource.py
```

任务：

- [ ] `/api/resource/generate` 接收 `path_id`。
- [ ] 校验 `path_id` 属于当前学生。
- [ ] 将 `path_id` 保存到每条新资源记录。
- [ ] 只为当前阶段第一个主要 topic 生成资源。
- [ ] 默认生成 5 类资源：document、exercise、code、mindmap、reading。
- [ ] 返回 `task_id`、`status=pending`、`progress=0`。
- [ ] 任务状态只使用 `pending/running/done/failed`。
- [ ] 任务进度包含 `progress`、`phase`、`message`、`result`、`error`。
- [ ] Agent 失败时进入规则化降级或 `failed`，不能永远停在 running。
- [ ] `done` 时资源已经完成数据库提交。
- [ ] `/api/resource/list` 可以按 `student_id` 返回数据库已有资源。

### 3.5 保证学习记录和评估闭环

负责文件：

```text
backend/api/evaluate_api.py
backend/services/evaluate_service.py
backend/models/evaluation.py
```

任务：

- [ ] 资源查看、完成和答题行为可以通过 `/api/evaluate/record` 保存。
- [ ] 记录包含 `student_id`、`resource_id`、`action`、`topic`、`score`、`time_spent`。
- [ ] `/api/evaluate/start` 根据真实学习记录生成并保存报告。
- [ ] `/api/evaluate/report/{student_id}` 返回最新报告。
- [ ] 报告包含 `overall_score`、`dimensions`、`weak_topics`、`suggestions`、`review_plan`。
- [ ] `review_plan` 包含 `topic`、`urgency`、`reason`、`recommended_resources`。
- [ ] 兼容现有 `retention`、`due_date` 字段，但不要求前端根据未冻结字段猜逻辑。

### 3.6 队长自动化测试

- [ ] 未传 `current_profile` 时能自动加载数据库画像。
- [ ] 未传 `history` 时能自动加载聊天历史。
- [ ] 完整度不会从 0.86 回退到 0.3。
- [ ] 画像每轮只新增一个正确版本。
- [ ] Planner 使用最新画像目标。
- [ ] Planner 输出可保存并再次读取。
- [ ] 资源保存后 `path_id` 不为空且归属正确。
- [ ] 任务可以从 pending/running 到 done/failed。
- [ ] 学习记录提交后评估报告可以刷新。
- [ ] 数据库初始化连续执行两次不重复污染固定数据。
- [ ] 执行队长范围 API、Service、E2E 和性能回归。
- [ ] 最后执行完整 `pytest test -q`。

### 3.7 队长交付物

- [ ] Swagger 中五大业务接口可运行。
- [ ] 画像三轮增量更新的 SSE 日志。
- [ ] 路径生成成功和失败样例。
- [ ] 资源任务从 0 到 100 的接口日志。
- [ ] 固定学生数据库检查结果。
- [ ] 完整测试结果。
- [ ] P0/P1 问题清单及负责人。
- [ ] 最终 main 合并和封版结论。

---

## 4. 队员 A 任务清单

分支：`feature/frontend-core`

负责范围：所有前端页面、组件、API 调用封装、SSE 展示、状态管理、真实接口联调和截图。

禁止修改：

- `backend/` 下任何文件。
- Agent 输出字段。
- 数据库结构。

### 4.1 修复 ChatBox 请求和取消逻辑

负责文件：

```text
frontend/src/components/ChatBox.jsx
frontend/src/hooks/useChat.js
frontend/src/api/profile.js
frontend/src/pages/ProfilePage.jsx
```

任务：

- [ ] 将 `AbortSignal` 传到 `fetch` 的 `signal` 字段。
- [ ] 点击停止后真正中断当前 SSE 请求。
- [ ] 保存当前前端消息历史。
- [ ] 请求画像接口时传 `history` 和 `current_profile`，作为服务端自动恢复的双保险。
- [ ] 正确解析 `chat`、`profile_update`、`error`、`done`。
- [ ] `done` 只表示本轮请求结束，不直接视为画像完成。
- [ ] 从 `profile_update` 中兼容读取外层或嵌套的 `completeness`。
- [ ] 保存 `profile`、`completeness`、`next_questions`。
- [ ] 显示画像完整度百分比。
- [ ] 显示后端返回的下一轮关键问题。
- [ ] 请求失败时显示错误和重试，不允许静默切换 Mock。

### 4.2 增加画像阶段前端状态机

前端状态：

```text
collecting       正在收集画像
ready            completeness >= 0.85，等待用户确认
planning         正在生成路径
generating       路径完成，资源任务进行中
active           学习旅程可使用
failed           流程失败，可重试
```

任务：

- [ ] `completeness < 0.85` 时保持 collecting。
- [ ] `completeness >= 0.85` 时进入 ready。
- [ ] ready 状态显示“画像信息已足够”。
- [ ] ready 状态显示“开启学习之旅”按钮。
- [ ] 不自动点击、不自动跳转，必须由用户确认。
- [ ] 用户仍可选择继续补充画像。
- [ ] 生成期间禁用重复点击。
- [ ] 页面刷新后调用 `GET /api/profile/{student_id}` 恢复状态。

### 4.3 处理两个 ChatBox 的职责冲突

- [ ] 画像采集阶段只显示主 ChatBox。
- [ ] FloatingChat 在画像阶段隐藏或禁用。
- [ ] 学习旅程 active 后，FloatingChat 改用 `/api/tutor/chat`。
- [ ] FloatingChat 不再调用 `/api/profile/chat`。
- [ ] Tutor 请求使用 `explanation_style`，不要给画像消息拼接辅导 Prompt。
- [ ] 主 ChatBox 和 FloatingChat 不共享错误的消息状态。

### 4.4 点击“开启学习之旅”后的调用顺序

必须严格按以下已有接口执行：

1. 调用 `POST /api/planner/generate`。
2. 请求只传 `student_id`；如传 goal，必须来自最新画像。
3. 解析 `start/delta/data/error/done`。
4. 收到 `data` 后保存路径并获取 `path_id`。
5. 读取 `current_stage` 对应阶段。
6. 选择当前阶段第一个主要 topic。
7. 调用 `POST /api/resource/generate`。
8. 请求中传入 `path_id`。
9. 获取 `task_id` 后轮询 `/api/task/{task_id}/status`。
10. 任务 done 后刷新路径、资源和评估报告。

禁止：

- [ ] 不允许硬编码“掌握高中数学核心知识”。
- [ ] 不允许聊天每完成一轮就自动生成路径。
- [ ] 不允许路径未保存就生成资源。
- [ ] 不允许资源生成请求缺少 `path_id`。

### 4.5 学习旅程页面

任务：

- [ ] 首次进入时并行读取路径、资源和评估报告。
- [ ] 当前关卡高亮。
- [ ] 已完成关卡打勾。
- [ ] 未解锁关卡置灰。
- [ ] 每关显示 title、topics、tasks、estimated_days/difficulty。
- [ ] 按 `resource.topic` 与 `stage.topics` 匹配资源。
- [ ] 当前关卡展示资源任务进度。
- [ ] 点击资源调用详情接口或使用列表中的 content 展示。
- [ ] 资源失败后显示重试按钮。
- [ ] 展示 `review_plan`，按 high/medium/low 显示优先级。
- [ ] 没有复习计划时显示明确空状态。

页面进入时读取：

```text
GET /api/planner/demo-student-01
GET /api/resource/list?student_id=demo-student-01
GET /api/evaluate/report/demo-student-01
```

### 4.6 学习行为同步

- [ ] 打开资源时可提交 `action=view`。
- [ ] 完成资源时提交 `action=complete`。
- [ ] 练习提交时记录 `action=answer` 和 score。
- [ ] 成功写入记录后调用 `/api/evaluate/start`。
- [ ] 再刷新 `/api/evaluate/report/{student_id}`。
- [ ] 不要求每次浏览都调用 EvaluateAgent，避免请求过多。

### 4.7 真实接口和构建要求

- [ ] `VITE_USE_MOCK=false`。
- [ ] Network 中所有主流程请求都走 `/api/...`。
- [ ] 接口失败不显示伪造成功数据。
- [ ] `npm run build` 通过。
- [ ] 1366×768 下主流程可操作。
- [ ] 移动端不要求精修，只保证不白屏和主要按钮可点击。

### 4.8 队员 A 交付物

- [ ] 画像采集中截图。
- [ ] 完整度达到 0.85 的截图。
- [ ] “开启学习之旅”按钮截图。
- [ ] 路径生成中截图。
- [ ] 资源任务进度截图。
- [ ] 路径 + 资源同页截图。
- [ ] 复习推荐截图。
- [ ] Tutor 流式回答截图。
- [ ] Network 真实接口截图。
- [ ] `npm run build` 日志。

---

## 5. 队员 B 任务清单

分支：`feature/ai-core`

负责范围：五个 Agent、Prompt、RAG、知识库、安全、AI 输出结构和 Agent 测试。

禁止修改：

- `frontend/` 下任何文件。
- `backend/api/`、`backend/services/`、数据库模型和任务管理器。
- 已冻结的 HTTP 路径和统一响应格式。

### 5.1 ProfileAgent 增量画像

负责文件：

```text
backend/agents/profile_agent.py
```

必须输出：

```text
student_id
profile
completeness
next_questions
```

其中 profile 至少包含：

```text
knowledge_level
learning_goal
learning_history
cognitive_style
weakness
interest
pace_preference（当前兼容字段）
```

任务：

- [ ] 正确读取 `current_profile`。
- [ ] 新信息明确时才覆盖旧值。
- [ ] 未提及字段保持旧值，不恢复默认值。
- [ ] weakness 和 interest 合并去重。
- [ ] completeness 按信息覆盖情况计算。
- [ ] completeness 不因本轮消息较短而主动降低。
- [ ] `<0.85` 时最多提出 2 个最关键问题。
- [ ] `>=0.85` 时 `next_questions=[]`。
- [ ] 回复中明确说明画像已经足够，可以生成学习路径。
- [ ] LLM 失败时的规则化降级也保持同样字段。
- [ ] 不新增 `profile_ready` Agent 字段或 SSE 类型。

### 5.2 PlannerAgent 路径输出

负责文件：

```text
backend/agents/planner_agent.py
```

必须输出：

```text
goal
stages
current_stage
estimated_days
```

每个 stage 必须包含：

```text
stage_id
title
objectives
topics
tasks
```

任务：

- [ ] 只根据画像中的学习目标、基础和薄弱点生成路径。
- [ ] 不生成与画像无关的高中数学默认路径。
- [ ] 路径控制在 3–5 个阶段。
- [ ] 第一阶段适合当天演示。
- [ ] 每阶段至少 1 个 topic。
- [ ] 每个 task 包含任务文本和推荐资源类型。
- [ ] LLM 输出解析失败时，规则化路径结构保持一致。

### 5.3 ResourceAgent 五类资源

负责文件：

```text
backend/agents/resource_agent.py
```

每条资源必须包含：

```text
type
title
topic
difficulty
content
```

任务：

- [ ] document 输出 Markdown。
- [ ] mindmap 输出 markmap 可解析的 Markdown 列表。
- [ ] exercise 输出合法 JSON 字符串。
- [ ] code 输出带代码块的 Markdown。
- [ ] reading 输出 Markdown。
- [ ] topic 必须与请求 topic 完全一致。
- [ ] 规则化降级与 LLM 成功结构一致。
- [ ] 修复当前 exercise 从 JSON 变成 Markdown导致的测试失败。
- [ ] 至少验证：机器学习入门、线性回归、梯度下降、逻辑回归、模型评估。

exercise 内容格式：

```json
[
  {
    "question": "问题",
    "options": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "答案解释"
  }
]
```

### 5.4 TutorAgent 与 RAG

负责文件：

```text
backend/agents/tutor_agent.py
backend/rag/
backend/safety/
data/knowledge/
```

任务：

- [ ] `/api/tutor/chat` 所需结构稳定。
- [ ] 输出 answer、explanation_style、references、diagrams。
- [ ] 支持 auto、analogy、formula、visual、story。
- [ ] references 包含 title、source、content、similarity。
- [ ] 正常学习问题不被安全过滤误伤。
- [ ] 检索无结果时明确说明没有可靠依据。
- [ ] ChromaDB 不可用时返回可解释降级，不中断 SSE。
- [ ] 准备固定问题：“请用类比解释梯度下降”。

### 5.5 EvaluateAgent 和复习计划

负责文件：

```text
backend/agents/evaluate_agent.py
对应 Agent 测试
```

必须输出：

```text
overall_score
dimensions
weak_topics
suggestions
review_plan
```

任务：

- [ ] review_plan 至少包含 topic、urgency、reason、recommended_resources。
- [ ] 保持现有 retention、due_date 输出兼容。
- [ ] 新学习内容不能立即进入 high urgency。
- [ ] 低分或较旧记录进入 high/medium。
- [ ] 测试日期使用相对时间或冻结时钟。
- [ ] 修复当前遗忘曲线固定日期测试失败。
- [ ] 无学习记录时不编造评分和薄弱点。

### 5.6 队员 B 测试和交付物

- [ ] 三轮增量画像 JSON。
- [ ] completeness 单调不回退样例。
- [ ] PlannerAgent 路径 JSON。
- [ ] 五类资源样例。
- [ ] exercise 可 `json.loads` 的证据。
- [ ] Tutor/RAG 引用样例。
- [ ] 安全正常/拦截样例。
- [ ] review_plan 样例。
- [ ] 关闭当前 3 个失败测试。
- [ ] Agent/RAG/安全测试通过日志。

---

## 6. 三人对接关系

| 对接项 | 队长负责 | 队员 A 负责 | 队员 B 负责 |
|---|---|---|---|
| 画像上下文 | 从 DB 加载历史与最新画像 | 同时传 history/current_profile | 正确增量合并 |
| 画像完成 | 保证 completeness 不回退 | 根据 `>=0.85` 显示按钮 | 输出稳定 completeness/next_questions |
| 路径生成 | 读取最新画像并保存路径 | 调用 Planner SSE 并展示 | Planner 输出稳定结构 |
| 资源生成 | task_id、进度、path_id 持久化 | 发起任务、轮询、展示 | 五类资源格式稳定 |
| Tutor | SSE 和错误合同 | FloatingChat 接 `/api/tutor/chat` | 回答、RAG、降级质量 |
| 学习评估 | 保存记录并生成报告 | 在关键行为后刷新报告 | review_plan 输出稳定 |
| 错误处理 | 统一 code/message | 显示错误和重试 | Agent 异常不泄露非法结构 |
| 最终验收 | 组织主流程和合并 | 页面、构建、截图 | Agent/RAG/安全证据 |

---

## 7. 一天执行时间表

### 08:30–09:00：同步与冻结

全员：

- [ ] `git checkout main`
- [ ] `git pull origin main`
- [ ] 切回个人功能分支。
- [ ] `git merge main`
- [ ] 三人确认本任务清单和 `docs/api.md`。
- [ ] 冻结字段，不再口头增加临时字段。

### 09:00–11:00：第一阶段并行开发

队长：

- 修复服务端画像上下文。
- 修复 completeness 回退。
- 确认 Planner 使用最新画像。

队员 A：

- ChatBox 状态机。
- AbortSignal。
- 完整度展示和开启按钮。

队员 B：

- ProfileAgent 增量逻辑。
- PlannerAgent 输出。
- 修复对应测试。

### 11:00：第一次强制联调

必须跑通：

```text
连续三轮聊天
→ 历史能够被下一轮使用
→ completeness 不回退
→ 达到 0.85
→ 出现“开启学习之旅”按钮
```

未通过时，三人停止后续功能，只修画像链路。

### 11:30–14:00：路径和资源联调

队长：

- 路径保存。
- path_id 返回。
- 资源 path_id 关联。
- 任务状态。

队员 A：

- 点击按钮生成路径。
- 收到路径后生成当前关卡资源。
- 展示任务进度。

队员 B：

- Planner 输出稳定。
- ResourceAgent 五类格式。
- exercise JSON 修复。

### 14:00：第二次强制联调

必须跑通：

```text
点击开启学习之旅
→ 生成并保存路径
→ 返回 path_id
→ 创建资源任务
→ 进度到 100%
→ 资源写入数据库
→ 页面显示当前关卡资源
```

### 14:30–16:00：Tutor、评估和复习联调

队长：

- 学习记录和评估接口。
- 统一错误格式。

队员 A：

- FloatingChat 接 Tutor。
- 显示 review_plan。
- 刷新路径/资源/评估。

队员 B：

- Tutor/RAG 样例。
- 遗忘曲线测试。
- 安全冒烟。

### 16:00：功能冻结

之后只修 P0/P1：

- 页面打不开。
- 接口 500。
- 画像无法完成。
- 路径无法生成或保存。
- 资源任务永远不结束。
- 路径和资源无法关联。
- 评估接口无法返回。
- `pytest` 或 build 失败。

### 16:00–18:00：全流程回归

固定路线：

1. 使用 `demo-student-01` 完成三轮画像。
2. 点击“开启学习之旅”。
3. 查看路径。
4. 等待当前关卡资源完成。
5. 打开资源。
6. 使用 Tutor 提问。
7. 提交一次学习记录。
8. 刷新评估和复习计划。

执行：

```bash
pytest test -q
cd frontend
npm run build
```

### 18:00–19:00：证据、PR 和封版

- [ ] 队员 A 提交页面截图和 build 日志。
- [ ] 队员 B 提交 Agent/RAG/安全样例和测试日志。
- [ ] 队长提交接口测试、数据库检查和已知问题。
- [ ] 队长依次 Review 队员 B、队长后端、队员 A 的变更。
- [ ] 所有 PR 合并后在 main 再执行完整回归。
- [ ] P0 必须清零，P1 必须有明确结论。
- [ ] 不满足门禁时禁止虚假标记封版完成。

---

## 8. 最终验收标准

- [ ] ChatBox 每轮请求能正常结束。
- [ ] 停止按钮能真正取消请求。
- [ ] 历史聊天和当前画像能够进入下一轮推理。
- [ ] completeness 不回退。
- [ ] completeness 达到 0.85 后显示“开启学习之旅”。
- [ ] 用户点击后使用最新画像生成路径。
- [ ] 不再硬编码高中数学目标。
- [ ] 路径包含稳定 stages/topics/tasks。
- [ ] 当前关卡资源自动启动生成。
- [ ] 资源正确保存 path_id。
- [ ] 资源任务能到 done 或 failed，不会永远 running。
- [ ] 路径、资源和复习计划同页展示。
- [ ] FloatingChat 使用 TutorAgent，不再修改学生画像。
- [ ] 学习行为能写入 learning_records。
- [ ] 评估和 review_plan 能刷新。
- [ ] `VITE_USE_MOCK=false` 主流程可用。
- [ ] Swagger 接口成功/失败样例可运行。
- [ ] `pytest test -q` 全部通过。
- [ ] `npm run build` 通过。
- [ ] 页面、接口、Agent 证据齐全。

---

## 9. 每人日报模板

```markdown
### 姓名 / 角色

#### 已完成
- 

#### 今日交付物
- Commit：
- PR：
- 截图/日志：

#### 对接记录
- 与谁对接：
- 对接字段/接口：
- 结论：

#### 当前问题
- 优先级：P0 / P1 / P2
- 问题：
- 负责人：
- 计划关闭时间：

#### 需要配合
- 

#### 明日计划
- 
```

