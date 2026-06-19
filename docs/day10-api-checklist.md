# Day10 队长接口检查清单

日期：2026-06-19  
负责人：队长

## 目标

完成画像、路径、资源、任务、问答、评估接口的第一轮合同检查，统一成功/失败格式，补齐 Swagger 示例和错误码说明。

## 统一响应格式

普通 JSON 成功：

```json
{"success": true, "data": {}, "message": "ok"}
```

普通 JSON 失败：

```json
{"success": false, "error": true, "code": "ERROR_CODE", "message": "错误描述"}
```

SSE 失败事件：

```text
data: {"type":"error","code":"ERROR_CODE","message":"错误描述"}

data: {"type":"done"}
```

## 错误码表

| code | HTTP | 使用场景 |
| --- | ---: | --- |
| `BAD_REQUEST` | 400 | 通用请求错误 |
| `VALIDATION_ERROR` | 422 | FastAPI 参数校验失败 |
| `PROFILE_NOT_FOUND` | 404 | 获取画像但学生画像不存在 |
| `PROFILE_UPDATE_EMPTY` | 400 | 更新画像时没有传任何字段 |
| `PROFILE_CHAT_FAILED` | 500 | 画像对话 SSE 失败 |
| `PATH_NOT_FOUND` | 404 | 获取学习路径但路径不存在 |
| `PLANNER_GENERATE_FAILED` | 500 | 路径生成 SSE 失败 |
| `PIPELINE_GENERATE_FAILED` | 500 | 画像到路径流水线失败 |
| `RESOURCE_NOT_FOUND` | 404 | 资源详情或收藏目标不存在 |
| `RESOURCE_GENERATE_FAILED` | 500 | 资源生成任务或 SSE 失败 |
| `TASK_NOT_FOUND` | 404 | 轮询不存在的异步任务 |
| `TUTOR_CHAT_FAILED` | 500 | 智能辅导 SSE 失败 |
| `EVALUATE_FAILED` | 500 | 流式评估失败 |
| `DATABASE_UNAVAILABLE` | 503 | 健康检查发现数据库不可用 |
| `INTERNAL_SERVER_ERROR` | 500 | 未捕获服务端异常 |

## 接口检查状态

| 模块 | 路径 | 成功格式 | 失败格式 | Swagger 示例 | 测试 |
| --- | --- | --- | --- | --- | --- |
| 健康检查 | `/api/health` | 已统一 | 已统一 | 已补齐 | `test_api_errors.py` |
| 画像 | `/api/profile/*` | 已统一 | 已统一 | 已补齐 | `test_api_contract.py`, `test_api_errors.py` |
| 路径 | `/api/planner/*` | 已统一 | 已统一 | 已补齐 | `test_api_errors.py`, `test_day11_e2e.py` |
| 资源 | `/api/resource/*`, `/api/resources/*` | 已统一 | 已统一 | 已补齐 | `test_api_contract.py`, `test_api_errors.py`, `test_day11_e2e.py` |
| 任务 | `/api/task/{task_id}/status` | 已统一 | 已统一 | 已补齐 | `test_api_contract.py`, `test_api_errors.py` |
| 问答 | `/api/tutor/*` | 已统一 | 已统一 | 已补齐 | `test_api_contract.py`, `test_day11_e2e.py` |
| 评估 | `/api/evaluate/*` | 已统一 | 已统一 | 已补齐 | `test_api_contract.py`, `test_api_errors.py`, `test_day11_e2e.py` |

## 前后端对齐记录

- 前端成功响应统一读取 `response.data.data`。
- 前端失败提示统一读取 `response.data.code` 和 `response.data.message`。
- SSE 错误统一从事件体读取 `type=error`、`code`、`message`。
- 联调时 `VITE_USE_MOCK=false`，接口失败不得静默降级到 Mock 数据。

## 验收命令

```powershell
pytest test/test_api_contract.py test/test_api_errors.py -q -p no:cacheprovider
```

Swagger 验收：

- `http://localhost:8000/docs`
- `http://localhost:8000/openapi.json`
