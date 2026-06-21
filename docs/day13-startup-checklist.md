# Day13 一键启动与初始化验收记录

日期：2026-06-21
负责人：队长

## 目标

让全队可以用同一套环境变量、数据库初始化脚本和启动命令运行项目；启动后 Swagger、健康检查和五条主业务链路都能访问。

## 新增启动入口

| 文件 | 用途 |
| --- | --- |
| `.env.example` | 全队统一环境变量模板，默认关闭前端 Mock，开启空库演示数据导入 |
| `scripts/init-db.ps1` | 按 `schema.sql` 建表并导入 `seed.sql`，输出核心表记录数 |
| `scripts/start-backend.ps1` | 初始化数据库并启动 FastAPI，默认端口 `8000` |
| `scripts/start-frontend.ps1` | 启动 Vite 前端，默认端口 `5173`，默认 `VITE_USE_MOCK=false` |
| `scripts/start-all.ps1` | 一键拉起前后端两个终端窗口 |
| `scripts/init-rag.ps1` | 复用队员B的 `knowledge_loader`，重复导入 `data/knowledge` 到 ChromaDB |
| `docker-compose.yml` | Docker Compose 启动后端和 Nginx 前端 |
| `backend/Dockerfile` | 后端容器构建文件 |
| `frontend/Dockerfile` / `frontend/nginx.conf` | 前端构建和容器内 `/api` 反向代理 |
| `data/sql/seed.sql` | 固定学生 `demo-student-01` 的画像、路径、资源和学习记录 |

## 本地一键启动

```powershell
cd C:\Users\26310\Desktop\GitHub\projectrjb
powershell -ExecutionPolicy Bypass -File scripts/start-all.ps1
```

启动后检查：

| 项目 | 地址 | 预期 |
| --- | --- | --- |
| 前端 | `http://localhost:5173` | 页面可以打开，Network 请求走真实 `/api` |
| Swagger | `http://localhost:8000/docs` | 能看到接口文档 |
| 健康检查 | `http://localhost:8000/api/health` | 返回 `success: true`、`database: ok` |
| 固定画像 | `http://localhost:8000/api/profile/demo-student-01` | 返回固定学生画像 |
| 固定路径 | `http://localhost:8000/api/planner/demo-student-01` | 返回 active 学习路径 |

## Docker Compose 启动

```powershell
cd C:\Users\26310\Desktop\GitHub\projectrjb
docker compose up --build
```

容器模式地址：

| 服务 | 地址 |
| --- | --- |
| 前端 | `http://localhost:3000` |
| 后端 Swagger | `http://localhost:8000/docs` |
| 后端健康检查 | `http://localhost:8000/api/health` |

如需配置真实 LLM 密钥，可先复制 `.env.example` 为 `.env` 并填入密钥；Compose 没有 `.env` 时也能使用默认降级配置启动。

配置解析检查：

```powershell
docker compose config
```

当前结果：

```text
配置解析通过
```

## 数据库初始化验收

固定种子数据包含：

| 表 | 验收点 |
| --- | --- |
| `students` | `demo-student-01` 存在 |
| `student_profiles` | 固定学生有画像、薄弱点和记忆强度 |
| `learning_paths` | 固定学生有 active 学习路径 |
| `resources` | 固定学生有一条讲义资源 |
| `learning_records` | 固定学生有一条完成记录 |

自动化检查：

```powershell
pytest test/test_day13_startup.py -q -p no:cacheprovider
```

当前结果：

```text
1 passed
```

脚本验收：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/init-db.ps1 -DatabasePath day13-startup-check.db
```

当前输出：

```text
students: 1
student_profiles: 1
learning_paths: 1
resources: 1
learning_records: 1
evaluation_reports: 0
```

## 五条业务 API 验收

| 流程 | 接口 | 预期 |
| --- | --- | --- |
| 画像 | `GET /api/profile/demo-student-01` | 返回真实画像，不依赖 Mock |
| 路径 | `GET /api/planner/demo-student-01` | 返回 active 学习路径 |
| 资源 | `POST /api/resource/generate` | 返回 `task_id`，轮询任务可完成 |
| 问答 | `POST /api/tutor/chat` | SSE 首帧可返回，失败时有明确错误 |
| 评估 | `POST /api/evaluate/start` | 返回评估报告并可读取历史 |

## RAG 初始化验收

知识库初始化命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/init-rag.ps1
```

预期日志：

```text
发现 N 个知识文件
知识库导入完成: N 个文件 -> M 个文本块
```

当前队长检查：

```text
scripts/init-rag.ps1 syntax ok
```

说明：

- 向量库目录统一读取 `CHROMA_PERSIST_DIR`，本地默认 `./data/chroma_db`。
- `scripts/start-all.ps1` 不自动重建 RAG，避免每次启动都重新跑 embedding；由队员B在知识库更新后执行初始化脚本。
- 如本地 embedding 模型首次下载较慢，完整 RAG 导入日志由队员B在 AI/RAG 环境补齐；问答接口仍需按降级策略处理 RAG 失败或无命中。

## 对接记录

- 队长 -> 队员A：前端开发默认端口 `5173`；本地通过 Vite proxy 访问 `http://localhost:8000/api`；Docker 前端通过 Nginx 代理 `/api` 到 backend 容器。
- 队长 -> 队员A：联调时保持 `VITE_USE_MOCK=false`，接口失败展示后端错误，不静默回退 Mock。
- 队长 -> 队员A：前端生产构建已通过 `npm run build`；当前只有 chunk 体积提示，不阻断 Day13 启动验收。
- 队长 -> 队员B：RAG 初始化目录统一使用 `CHROMA_PERSIST_DIR`；知识库更新后运行 `scripts/init-rag.ps1`；知识库未初始化时，问答接口仍应通过降级策略返回可解释错误或基础回答。
- 全员：Day13 验收以同一份 `.env.example` 和 `scripts/start-all.ps1` 为准。

## 自动化验收汇总

```powershell
pytest test -q -p no:cacheprovider
```

当前结果：

```text
137 passed
```

```powershell
npm run build
```

当前结果：

```text
vite build completed successfully
```
