# Day 16 最终技术验收与封版门禁

> 执行日期：2026-07-15  
> 执行分支：`feature/backend-core`  
> 固定演示学生：`demo-student-01`

## 1. 当前结论

当前版本的后端启动、数据库、画像读取、路径读取、资源列表、异步资源生成、评估报告和任务轮询主链路可运行。前端生产构建通过。

当前版本**暂不满足最终封版条件**，原因是完整后端测试仍有 3 项失败，且本机 RAG 依赖未就绪。必须由对应负责人关闭后，再执行最终合并。

## 2. 队长验收结果

| 检查项 | 结果 | 证据/说明 |
|---|---|---|
| 分支同步 | 通过 | `feature/backend-core` 已合并 `origin/main@3af27b4` |
| 后端启动 | 通过 | `http://127.0.0.1:8000` 可访问 |
| 前端启动 | 通过 | `http://127.0.0.1:5173` 返回 HTTP 200 |
| 健康检查 | 通过 | `/api/health` 返回 `success=true`、`database=ok` |
| 固定学生 | 通过 | `/api/profile/demo-student-01` 返回有效画像 |
| 学习路径 | 通过 | 返回 2 个阶段，包含冻结字段 |
| 学习资源 | 通过 | 验收时资源列表已有 39 条；实际生成后新增 1 条 |
| 异步任务 | 通过 | `task_eb9adf1a` 最终 `done`、`progress=100`，资源成功落库 |
| 评估报告 | 通过 | 返回 2 条 `review_plan`，包含 `retention` 与 `due_date` |
| 队长范围测试 | 通过 | API/Service/E2E/Performance/Day15 回归：`21 passed` |
| 完整后端测试 | 未通过 | `134 passed, 3 failed`，失败均位于队员 B 的 Agent/test 范围 |
| 前端生产构建 | 通过 | `npm.cmd run build` 成功，Vite 生成生产产物 |
| Docker Compose 配置 | 通过 | `docker compose config --quiet` 可解析 |
| 示例密钥检查 | 已修复 | `backend/.env.example` 的真实星火凭证已清空；旧凭证仍需控制台轮换 |

## 3. 学习旅程接口冻结表

冻结后字段不得单方面变更；如需变更，必须由队长、队员 A、队员 B 同时确认。

| 用途 | 方法与路径 | 冻结响应字段 |
|---|---|---|
| 获取学习路径 | `GET /api/planner/demo-student-01` | `stages[]`, `current_stage`; stage: `stage_id`, `title`, `description`, `objectives`, `topics`, `estimated_days`, `difficulty`, `tasks` |
| 获取学习资源 | `GET /api/resources/list?student_id=demo-student-01` | `items[]`; item: `id`, `student_id`, `path_id`, `type`, `title`, `topic`, `difficulty`, `content`, `is_review` |
| 获取复习计划 | `GET /api/evaluate/report/demo-student-01` | `review_plan[]`; item: `topic`, `urgency`, `reason`, `recommended_resources`, `retention`, `due_date`, `days_since_last_study`, `estimated_minutes` |
| 生成关卡资源 | `POST /api/resource/generate` | 请求：`student_id`, `topic`, `types`, `difficulty`, `count`, `path_id`; 响应：`task_id`, `status` |
| 查询任务进度 | `GET /api/task/{task_id}/status` | `status`, `progress`, `phase`, `message`, `result`, `error`, `progress_history` |
| 智能辅导 | `POST /api/tutor/chat` | SSE：`start`, `delta`, `data`, `error`, `done` |

## 4. 实际演示数据

| 数据 | 验收结果 |
|---|---|
| 画像 | `demo-student-01` 可读取，包含知识基础、目标、历史、认知风格、薄弱点、兴趣、记忆强度和完整度 |
| 路径 | 2 个学习阶段，首阶段包含 `stage_id/title/topics/tasks` |
| 资源 | 列表接口可返回资源；异步任务可生成并持久化 document 资源 |
| 复习 | 2 条复习计划，包含优先级、推荐资源、保留率和到期日期 |

## 5. 未关闭问题与负责人

### P0：必须在最终提交前关闭

1. **轮换已泄露的星火凭证（队长）**  
   模板中的凭证已删除并提交，但旧值已进入 Git 历史。必须在讯飞控制台作废旧凭证并创建新凭证，新值只写入本地 `.env`。

2. **完整测试必须全绿（队员 B）**  
   当前 `pytest test -q` 为 `134 passed, 3 failed`：
   - `ResourceAgent` 的 `exercise.content` 当前输出 Markdown，但冻结契约和测试要求 JSON，导致 2 项失败。
   - 遗忘曲线测试把 `2026-06-20` 写死为“今天”，当前日期运行产生 1 项失败；测试数据必须改为相对当前时间，或冻结测试时钟。

### P1：提交前优先关闭

1. **RAG 本机依赖未就绪（队员 B）**  
   启动日志显示 `chromadb 未安装`，当前会走可解释降级。需要按 `backend/requirements.txt` 安装依赖并保留一次知识库加载与检索日志。

2. **资源生成耗时与回退（队员 B）**  
   实际资源任务耗时约 59 秒，LLM 输出不是合法 JSON，最终回退规则模板。主链路未阻断，但演示前应保证固定主题可稳定生成，或明确使用演示降级数据。

3. **学习旅程页面证据未收齐（队员 A）**  
   队员 A 需提交“开启学习之旅”、关卡页、关卡资源、复习推荐四张截图，并证明 `VITE_USE_MOCK=false`。

## 6. 最终封版门禁

只有以下条件全部满足，队长才允许合并最终版本：

- [ ] `pytest test -q` 全部通过。
- [x] 队长范围 API/服务/E2E/性能测试通过。
- [x] `npm run build` 通过。
- [x] 固定学生、数据库和后端启动链路可用。
- [x] 学习路径、资源、复习计划字段已冻结。
- [x] 异步资源任务可到达 `done=100%` 并返回结果。
- [ ] 队员 A 提交学习旅程四张验收截图和真实接口证据。
- [ ] 队员 B 提交 5 类资源、RAG、安全、遗忘曲线证据并关闭 3 个失败测试。
- [ ] 星火旧凭证已在控制台轮换。
- [ ] 最终已知问题只剩不影响演示的 P2/P3。

## 7. 最终演示路线

1. 使用固定学生 `demo-student-01` 完成画像对话。
2. 打开学习路径并展示阶段、知识点和任务。
3. 进入学习旅程，展示关卡状态和匹配资源。
4. 缺资源时触发异步生成，展示任务进度到 100%。
5. 打开资源内容，展示 Markdown/代码/练习。
6. 进入智能辅导，展示流式回答和引用/降级说明。
7. 打开评估报告，展示评分、薄弱点和 `review_plan`。

