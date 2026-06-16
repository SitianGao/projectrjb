# EduAgent API Contract

本文档是前后端对接的唯一 API 标准。后端以 `http://127.0.0.1:8000/docs` 和 `http://127.0.0.1:8000/openapi.json` 为准；前端不得再按 Mock 数据自行猜接口。

## 0. 本地运行与配置

后端：

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

前端 Vite 代理：

```js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

每位队员本地都需要自己的 `backend/.env`，不要提交到 Git：

```env
LLM_PRIMARY=spark
SPARK_API_PASSWORD=...
SPARK_API_URL=https://spark-api-open.xf-yun.com/v1/chat/completions
SPARK_MODEL=4.0Ultra
DATABASE_URL=sqlite:///./eduagent.db
```

修改 `.env` 后必须重启后端。

## 1. 通用约定

- Base URL: `/api`
- JSON 请求头: `Content-Type: application/json`
- SSE 响应头: `Content-Type: text/event-stream`
- 普通 JSON 成功响应统一包装：

```json
{"success": true, "data": {}, "message": "ok"}
```

- 普通 JSON 失败响应统一包装：

```json
{"success": false, "error": true, "code": "ERROR_CODE", "message": "错误描述"}
```

- 第一阶段为避免旧前端立刻挂掉，后端会临时把 `data` 对象里的业务字段同步放在顶层；正式新调用请统一读取 `response.data.data`。
- SSE 事件格式统一为：

```text
data: {"type":"start","message":"..."}

data: {"type":"chat","content":"..."}

data: {"type":"data","data":{}}

data: {"type":"error","code":"...","message":"..."}

data: {"type":"done"}
```

- FastAPI 参数校验失败返回 `422`，格式同统一失败响应。
- 未找到资源返回 `404`：

```json
{"success":false,"error":true,"code":"NOT_FOUND","message":"资源不存在或任务不存在"}
```

## 2. Profile API

### POST `/api/profile/chat`

对话式画像构建，SSE 流式返回。

请求：

```json
{
  "student_id": "demo-student-01",
  "message": "我想提高高中数学",
  "history": ["上一轮对话，可选"],
  "current_profile": {}
}
```

SSE 事件：

```text
data: {"type":"start","message":"开始分析学习画像"}
data: {"type":"chat","content":"..."}
data: {"type":"profile_update","profile":{}}
data: {"type":"done"}
```

### GET `/api/profile/{student_id}`

获取学生画像。

成功返回：

```json
{
  "success": true,
  "data": {
    "student_id": "demo-student-01",
    "profile": {},
    "completeness": 0.8,
    "next_questions": []
  },
  "message": "ok"
}
```

### PUT `/api/profile/{student_id}`

增量更新画像。

请求：

```json
{
  "knowledge_level": "中级",
  "learning_goal": "掌握高中数学核心知识",
  "cognitive_style": "实践型",
  "weakness": ["函数", "几何"],
  "interest": ["AI", "编程"],
  "pace_preference": "每天 30 分钟"
}
```

成功返回：统一响应包装后的更新画像对象。

## 3. Planner API

### POST `/api/planner/generate`

生成学习路径，SSE 流式返回。

请求：

```json
{
  "student_id": "demo-student-01",
  "goal": "掌握高中数学核心知识"
}
```

SSE 事件：

```text
data: {"type":"start","message":"开始生成个性化学习路径"}
data: {"type":"delta","content":"..."}
data: {"type":"data","data":{"student_id":"...","stages":[]}}
data: {"type":"done"}
```

### GET `/api/planner/{student_id}`

获取当前学习路径。

## 4. Resource API

资源类型标准值：

```text
document | exercise | code | mindmap | reading
```

前端旧值 `quiz` 需要改成 `exercise`。

### POST `/api/resource/generate`

异步生成学习资源，立即返回 `task_id`。

请求：

```json
{
  "student_id": "demo-student-01",
  "topic": "机器学习入门",
  "types": ["document", "exercise", "code"],
  "difficulty": "初级",
  "count": 1,
  "path_id": null
}
```

成功返回：

```json
{
  "success": true,
  "data": {
    "task_id": "task_abc12345",
    "status": "pending",
    "progress": 0,
    "message": "资源生成任务已创建",
    "result": null,
    "error": null,
    "created_at": "2026-06-15T14:00:00Z",
    "updated_at": "2026-06-15T14:00:00Z"
  },
  "message": "资源生成任务已创建",
  "task_id": "task_abc12345",
  "status": "pending",
  "progress": 0,
  "result": null,
  "error": null
}
```

### POST `/api/resource/generate/stream`

流式生成学习资源。

请求同 `/api/resource/generate`。

SSE 事件：

```text
data: {"type":"start","message":"开始生成..."}
data: {"type":"progress","progress":0.8,"message":"资源生成完成，正在整理结果"}
data: {"type":"data","data":{"topic":"...","items":[],"resources":[]}}
data: {"type":"done"}
```

### GET `/api/resource/list`

获取资源列表。

Query:

```text
student_id 可选
page 默认 1
page_size 默认 20
keyword 可选
type 可选，document/exercise/code/mindmap/reading
```

成功返回：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "student_id": "demo-student-01",
        "type": "document",
        "title": "机器学习入门指南",
        "topic": "机器学习入门",
        "difficulty": "初级",
        "description": "内容摘要",
        "tags": ["机器学习入门", "初级", "document"],
        "content": "Markdown 正文",
        "created_at": "2026-06-15T14:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  },
  "message": "ok"
}
```

### GET `/api/resource/{resource_id}`

获取资源详情。

## 5. Tutor API

### POST `/api/tutor/chat`

智能辅导问答，SSE 流式返回。

请求：

```json
{
  "student_id": "demo-student-01",
  "message": "请解释一下二次函数顶点式",
  "session_id": "可选",
  "history": ["可选历史消息"]
}
```

SSE 事件：

```text
data: {"type":"start","session_id":"...","message":"开始生成辅导回复"}
data: {"type":"chat","content":"..."}
data: {"type":"error","code":"LLM_ERROR","message":"..."}
data: {"type":"done","session_id":"..."}
```

### GET `/api/tutor/sessions?student_id=demo-student-01`

获取辅导会话列表。

### POST `/api/tutor/sessions`

创建辅导会话。

请求：

```json
{
  "student_id": "demo-student-01",
  "title": "二次函数答疑"
}
```

## 6. Evaluate API

### POST `/api/evaluate/start`

开始或刷新学习评估。

请求：

```json
{"student_id":"demo-student-01"}
```

成功返回：评估报告，结构同 `/api/evaluate/report/{student_id}`。

### GET `/api/evaluate/report/{student_id}`

获取评估报告。

成功返回：

```json
{
  "success": true,
  "data": {
    "student_id": "demo-student-01",
    "overall_score": 78,
    "recent_trend": "up",
    "completed_tasks": 24,
    "total_time": 129600,
    "topic_scores": [
      {"topic":"二次函数","score":85,"level":"优秀"}
    ],
    "history": [
      {"date":"2026-06-15","score":78,"tasks":3}
    ],
    "progress_stats": {
      "total_topics": 12,
      "mastered_topics": 5,
      "learning_topics": 4,
      "not_started_topics": 3
    }
  }
}
```

### GET `/api/evaluate/progress/{student_id}`

获取学习进度统计。

### POST `/api/evaluate/record`

提交学习记录。

请求：

```json
{
  "student_id": "demo-student-01",
  "resource_id": "可选",
  "action": "complete",
  "topic": "二次函数",
  "score": 85,
  "time_spent": 1800
}
```

## 7. Task API

### GET `/api/task/{task_id}/status`

查询异步任务状态。

成功返回：

```json
{
  "success": true,
  "data": {
    "task_id": "task_abc12345",
    "status": "pending|running|done|failed",
    "progress": 80,
    "message": "正在生成学习资源",
    "result": {},
    "error": null,
    "created_at": "2026-06-15T14:00:00Z",
    "updated_at": "2026-06-15T14:00:01Z"
  },
  "message": "ok"
}
```

## 8. 前端队员必须修改的调用点

队员 A 负责修改 `frontend/src/api/*.js` 和相关页面 Mock 开关：

| 文件 | 当前问题 | 必改为 |
| --- | --- | --- |
| `frontend/src/api/client.js` | 直接把后端响应交给页面 | 统一解包 `response.data.data`，错误读 `code/message` |
| `frontend/src/api/resource.js` | 使用 `/resources`、`/resources/generate/stream` | `/resource/list`、`/resource/generate`、`/resource/generate/stream` |
| `frontend/src/api/tutor.js` | 使用 `/tutor/ask/stream` | 正式改 `/tutor/chat`；短期后端保留 `/tutor/ask/stream` 兼容 |
| `frontend/src/api/evaluate.js` | 使用 `/evaluate/{id}`、`/evaluate/{id}/progress`、`/evaluate/generate` | 正式改 `/evaluate/report/{id}`、`/evaluate/progress/{id}`、`/evaluate/start`；短期后端保留旧路由兼容 |
| 页面 Mock | 接口失败后静默降级 Mock，掩盖真实错误 | 加 `VITE_USE_MOCK=true/false`，联调时必须 `false` |
| 资源类型 | 使用 `quiz` | 使用 `exercise` |

联调验收顺序：

1. 后端 `/docs` 能打开。
2. 前端 `/api/...` 请求能从 Network 里看到 200 或明确 4xx/5xx。
3. 关闭 Mock 后，画像 -> 路径 -> 资源 -> 辅导 -> 评估主流程可以连续运行。
