# Day11 固定学生 E2E 验收清单

日期：2026-06-19  
负责人：队长  
固定学生：`demo-student-01`

## 目标

用固定测试学生打通主流程，并留下可复跑的测试和手工验收步骤：画像 -> 路径 -> 资源 -> 问答 -> 评估。

## 自动化验收

```powershell
pytest test/test_day11_e2e.py -q -p no:cacheprovider
```

测试覆盖：

| 步骤 | 接口 | 期望 |
| --- | --- | --- |
| 健康检查 | `GET /api/health` | 后端和数据库均可用 |
| 画像 | `GET /api/profile/demo-student-01` | 返回固定学生画像 |
| 路径 | `GET /api/planner/demo-student-01` | 返回 active 学习路径 |
| 资源 | `POST /api/resource/generate` + `GET /api/task/{task_id}/status` | 资源生成任务完成并落库 |
| 问答 | `POST /api/tutor/chat` | SSE 返回 `start/data/done`，包含 RAG references |
| 评估 | `POST /api/evaluate/record` + `POST /api/evaluate/start` | 生成并保存评估报告 |
| 报告读取 | `GET /api/evaluate/report/demo-student-01` | 能读取刚生成的报告 |

## 手工 E2E 步骤

1. 启动后端：

```powershell
cd projectrjb/backend
uvicorn app:app --reload
```

2. 启动前端：

```powershell
cd projectrjb/frontend
npm run dev
```

3. 确认前端关闭 Mock：

```env
VITE_USE_MOCK=false
```

4. 打开 Swagger：

```text
http://localhost:8000/docs
```

5. 打开健康检查：

```text
http://localhost:8000/api/health
```

6. 使用固定学生 `demo-student-01` 依次检查：

| 页面/功能 | 操作 | 期望 |
| --- | --- | --- |
| 画像页 | 读取或刷新画像 | Network 显示 `/api/profile/demo-student-01`，页面显示真实画像字段 |
| 学习路径页 | 查看当前路径 | Network 显示 `/api/planner/demo-student-01`，页面显示阶段和任务 |
| 资源页 | 生成或查看资源 | Network 显示 `/api/resource/generate` 或 `/api/resource/list`，任务完成后有资源 |
| 问答页 | 提问“请解释梯度下降” | Network 显示 `/api/tutor/chat` 或兼容 `/api/tutor/ask/stream`，SSE 返回答案 |
| 评估页 | 提交记录并生成报告 | Network 显示 `/api/evaluate/record` 和 `/api/evaluate/start`，页面显示评分和复习建议 |

## 截图清单

| 截图名 | 内容 |
| --- | --- |
| `day11-01-health.png` | `/api/health` 返回 `success=true` |
| `day11-02-profile.png` | 固定学生画像页面 |
| `day11-03-path.png` | 学习路径阶段页面 |
| `day11-04-resource.png` | 资源列表或资源生成完成状态 |
| `day11-05-tutor.png` | 问答 SSE 返回答案 |
| `day11-06-evaluate.png` | 评估报告页面 |

## P0 / P1 问题记录

| 级别 | 问题 | 当前状态 |
| --- | --- | --- |
| P0 | 主流程不能在关闭 Mock 后完成 | 待手工联调确认 |
| P0 | 接口失败没有 `code/message` | 自动化测试已覆盖 |
| P1 | 页面文案没有使用后端 `message` | 待前端队员确认 |
| P1 | 截图缺失或 Network 未展示真实接口 | 待手工验收补齐 |

## 不依赖 Mock 确认

- 后端固定学生数据由 `test/support/demo_data.py` 保底创建。
- 自动化 E2E 走真实 FastAPI 路由和真实数据库。
- 测试中只替换大模型/RAG 返回，避免外部网络影响；不替换画像、路径、资源、任务、评估接口。
- 前端联调必须设置 `VITE_USE_MOCK=false`，接口失败时显示后端 `message`，不得静默回退 Mock。
