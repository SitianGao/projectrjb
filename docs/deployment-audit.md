# EduAgent 部署审计报告

**审计日期：** 2026-07-20
**审计范围：** projectrjb 项目全量部署相关文件

---

## 1. docker-compose.yml 能否正常运行

**文件：** `projectrjb/docker-compose.yml`

**现状：**
- 定义了 `backend` 和 `frontend` 两个服务
- backend 使用 `backend/Dockerfile`，build context 为项目根目录
- frontend 使用 `frontend/Dockerfile`，build context 为项目根目录
- 共享 `backend-runtime` 命名卷

**问题：**
- ❌ build context 是 `.`（项目根目录），但 Dockerfile 中 COPY 路径假设 context 是根目录，这在 `projectrjb/` 目录内执行 `docker compose up` 时是正确的
- ❌ 没有 healthcheck 配置
- ❌ 没有 restart policy
- ❌ 没有资源限制
- ❌ frontend 的 `depends_on` 没有 `condition: service_healthy`
- ⚠️ 环境变量直接引用 `.env` 文件中的密钥，会泄露到镜像层

**结论：** 基本可运行，但不适合生产交付。

---

## 2. backend/Dockerfile 生产适用性

**文件：** `projectrjb/backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY data data
COPY .env.example .env.example
EXPOSE 8000
CMD ["uvicorn", "app:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
```

**问题：**
- ❌ 没有 `.dockerignore` 筛选（虽然根目录有 `.dockerignore`，但不够完善）
- ❌ 没有 multi-stage build，镜像体积大
- ❌ 没有 HEALTHCHECK 指令
- ❌ 没有非 root 用户
- ❌ `COPY data data` 会拷贝整个知识库 + chroma_db（约 20MB+），但 chroma_db 应该用卷挂载
- ⚠️ sentence-transformers 模型首次启动需要联网下载（约 120MB）
- ⚠️ 没有固定 pip 镜像源，国内构建可能慢

**必须修改项：**
1. 添加 HEALTHCHECK
2. 添加非 root 用户
3. 分离 chroma_db 为卷挂载
4. 预下载嵌入模型或提供离线方案

---

## 3. frontend/Dockerfile 生产适用性

**文件：** `projectrjb/frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
RUN npm run build

FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

**评价：**
- ✅ 使用 multi-stage build（正确）
- ✅ 先 COPY package.json 再 npm install（利用 Docker 缓存）
- ✅ 最终镜像只包含 nginx + 静态文件

**问题：**
- ❌ 没有 HEALTHCHECK
- ❌ 没有配置 nginx 缓存策略
- ❌ 没有 gzip 压缩配置
- ⚠️ `npm install` 而非 `npm ci`，构建不可复现

**必须修改项：**
1. 改用 `npm ci`
2. 添加 HEALTHCHECK
3. 添加 gzip 和缓存配置

---

## 4. nginx.conf 反向代理配置

**文件：** `projectrjb/frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_buffering off;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**评价：**
- ✅ `/api/` 正确反向代理到 backend:8000
- ✅ `proxy_buffering off` 支持 SSE 流式
- ✅ SPA fallback `try_files` 正确

**问题：**
- ❌ 缺少 `/docs` 和 `/openapi.json` 的代理（Swagger UI 需要）
- ❌ 缺少生成资源下载路径代理（如 `/storage/` 或 `/api/ppt/download`）
- ❌ 没有 gzip 压缩
- ❌ 没有静态资源缓存头
- ❌ 没有 SSE 特定的超时配置（`proxy_read_timeout`）
- ❌ 没有请求体大小限制

**必须修改项：**
1. 确保 SSE 长连接不超时（`proxy_read_timeout 300s`）
2. 添加 gzip 压缩
3. 添加静态资源缓存

---

## 5. WebSocket / 长连接配置

**现状：**
- 项目使用 SSE（Server-Sent Events）而非 WebSocket
- 前端通过 `fetch` + `ReadableStream` 处理 SSE
- 后端使用 `sse-starlette` 库
- nginx 的 `proxy_buffering off` 已正确配置

**结论：** 无 WebSocket，SSE 配置基本正确，但需要增加超时时间。

---

## 6. 后端实际启动命令

**Docker 中：**
```
uvicorn app:app --app-dir backend --host 0.0.0.0 --port 8000
```

**本地开发（PowerShell）：**
```
uvicorn app:app --reload --port 8000 --app-dir backend
```

**评价：** ✅ 生产环境应去掉 `--reload`，当前 Dockerfile 已正确。

---

## 7. 后端健康检查接口

| 路径 | 功能 | 依赖检查 |
|------|------|----------|
| `GET /` | 基础健康检查 | 无 |
| `GET /api/health` | 深度健康检查 | SQLite `SELECT 1` |

**结论：** ✅ 有可用的健康检查端点。Docker HEALTHCHECK 应使用 `/api/health`。

---

## 8. 前端 API Base URL 来源

**Axios 客户端（`src/api/client.js`）：**
```js
baseURL: '/api'  // 相对路径
```

**Vite 开发代理（`vite.config.js`）：**
```js
proxy: { '/api': { target: 'http://localhost:8000' } }
```

**Nginx 生产代理：**
```nginx
location /api/ { proxy_pass http://backend:8000/api/; }
```

**结论：** ✅ 前端完全使用相对路径 `/api`，无硬编码 URL。生产环境通过 nginx 反代正确路由。

---

## 9. 数据库真实使用位置

| 路径 | 大小 | 用途 |
|------|------|------|
| `projectrjb/eduagent.db` | 544 KB | 项目级（可能是开发残留） |
| `projectrjb/backend/eduagent.db` | 2.7 MB | **实际使用**（config.py 默认 `sqlite:///./eduagent.db`，工作目录为 backend/） |
| `c:/Users/26310/Desktop/GitHub/eduagent.db` | 442 KB | 根目录（开发残留） |

**Docker 中：** `DATABASE_URL=sqlite:////app/runtime/eduagent.db`，挂载到 `backend-runtime` 卷。

**结论：** 生产环境使用 `/app/runtime/eduagent.db`，通过卷持久化。本地开发使用 `backend/eduagent.db`。

---

## 10. ChromaDB 真实使用位置

| 路径 | 用途 |
|------|------|
| `projectrjb/data/chroma_db/` | 主 ChromaDB 向量库（约 20MB，含完整知识库向量） |
| `projectrjb/backend/data/chroma_db/` | 后端级（可能是独立初始化的） |

**config.py 配置：**
```python
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
```

**Docker 中：** `CHROMA_PERSIST_DIR=/app/runtime/chroma_data`

**结论：** 生产环境需要将 `data/chroma_db/` 预置到容器中或通过卷挂载。

---

## 11. 知识库真实使用位置

**主知识库：** `projectrjb/data/knowledge/`
- 131 个 Markdown 文件
- 15+ 子目录（AI导论、数学基础、机器学习、深度学习、NLP、CV 等）

**rag/knowledge_loader.py 引用：** 通过 `PROJECT_ROOT / "data" / "knowledge"` 定位。

**结论：** ✅ 知识库路径正确，Dockerfile 中 `COPY data data` 已包含。

---

## 12. 生成资源目录

| 路径 | 用途 |
|------|------|
| `projectrjb/data/generated_resources/` | Agent 生成的资源（含 smoke-ppt.pptx） |
| `projectrjb/backend/storage/ppt/` | PPT 下载目录 |

**结论：** 生产环境需要持久化这两个目录。

---

## 13. 日志目录

| 路径 | 大小 | 说明 |
|------|------|------|
| `projectrjb/logs/backend-dev.err.log` | **~39 GB** | ⚠️ 极大的错误日志 |
| `projectrjb/logs/eduagent.log` | ~4 MB | 主日志 |
| `projectrjb/backend/logs/` | 小 | 后端级日志 |
| `c:/Users/26310/Desktop/GitHub/logs/` | 113 KB | 根目录日志 |

**结论：** ⚠️ 39GB 的日志文件必须在打包前清理。`.gitignore` 已排除 `logs/`。

---

## 14. 嵌入模型首次启动是否需要联网

**模型：** `paraphrase-multilingual-MiniLM-L12-v2`（~120MB）

**现状：**
- `.env` 中设置了 `HF_HUB_OFFLINE=1` 和 `TRANSFORMERS_OFFLINE=1`
- 但模型文件需要预先下载到本地缓存

**结论：** ⚠️ 如果 HuggingFace 缓存中没有模型，首次启动需要联网。Docker 镜像应预下载模型。

---

## 15. Docker 中访问外部大模型

**现状：**
- 讯飞星火 API：`https://spark-api-open.xf-yun.com/v1/chat/completions`
- DeepSeek API：`https://api.deepseek.com`
- 需要外网访问

**结论：** ✅ Docker 默认支持外网访问。但需要用户提供有效的 API Key。

---

## 16. 判题服务依赖与安全

**依赖：**
- Docker 沙箱模式：需要 Docker Engine
- Subprocess 降级模式：需要 gcc/g++/javac/python3

**安全边界：**
- 代码长度限制：65536 字节
- 时间限制：2 秒/题
- 内存限制：256MB
- 禁止模式检查（fork/exec/system/socket 等）
- Docker 模式：`--network none`、`--read-only`、`--pids-limit=50`

**结论：** ✅ 安全设计合理。生产环境应使用 Docker 沙箱模式。

---

## 17. 重复文件分析

| 文件 | 是否被使用 | 说明 |
|------|-----------|------|
| 根目录 `eduagent.db` | ❌ 开发残留 | 可删除 |
| `backend/eduagent.db` | ✅ 本地开发使用 | config.py 默认路径 |
| `frontend/eduagent.db` | ❌ 误放入 | 在 src/ 下，不应存在 |
| `data/chroma_db` | ✅ 主向量库 | RAG 使用 |
| `backend/data/chroma_db` | ⚠️ 可能重复 | 需确认是否被引用 |
| 根目录 `.env` | ✅ 开发使用 | 包含真实密钥 |
| `backend/.env` | ✅ 开发使用 | 包含真实密钥 |

---

## 18. 现有脚本有效性

**`scripts/` 目录（PowerShell）：**
- `start-all.ps1` — 本地开发启动（有效）
- `start-backend.ps1` — 启动后端（有效）
- `start-frontend.ps1` — 启动前端（有效）
- `init-db.ps1` — 初始化数据库（有效）
- `init-rag.ps1` — 初始化 RAG（有效）

**评价：** ✅ 本地开发脚本有效，但没有 Docker 部署脚本。

---

## 19. 依赖版本锁定

**`backend/requirements.txt`：**
- 使用范围版本（如 `fastapi>=0.115,<1`）
- 没有 `requirements.lock` 或 `pip freeze` 输出

**`frontend/package.json`：**
- 有 `package-lock.json` ✅

**结论：** ⚠️ Python 依赖未完全锁定，可能导致构建不可复现。

---

## 20. 敏感信息与临时文件

**敏感信息：**
- ❌ `projectrjb/.env` 包含讯飞星火真实 API Key/Secret/Password
- ❌ `projectrjb/backend/.env` 包含相同的真实凭证
- ❌ 这两个文件在 `.gitignore` 中已排除，但会在打包时被包含

**临时文件/缓存：**
- ❌ `projectrjb/logs/backend-dev.err.log`（~39GB）
- ❌ `__pycache__/`、`.pytest_cache/`、`.vite/`、`node_modules/`
- ❌ `frontend/dist/`（构建产物）
- ❌ `frontend/src/eduagent.db`（误放入的数据库）
- ❌ `.idea/`、`.vscode/`（IDE 配置）
- ❌ `stickynotes/`（无关项目）

**结论：** 打包前必须清理所有敏感信息和临时文件。

---

## 当前调用关系

```
浏览器 → nginx:80 → /api/* → backend:8000
                    /*      → 静态文件 (SPA)

backend:8000
  ├── FastAPI app.py
  ├── agents/ (Profile, Planner, Resource, Tutor, Evaluate)
  ├── rag/ (ChromaDB + sentence-transformers)
  ├── services/ (各业务服务)
  ├── api/ (14 个路由模块)
  └── SQLite (eduagent.db)

外部依赖：
  ├── 讯飞星火 LLM API
  ├── 讯飞 PPT API
  ├── DeepSeek API（备用）
  └── HuggingFace（嵌入模型下载）
```

## 当前路径关系

```
projectrjb/                    ← 项目根目录（git 仓库）
├── .env                       ← 项目级环境变量（含密钥）
├── docker-compose.yml         ← 开发用 compose
├── backend/
│   ├── .env                   ← 后端环境变量（含密钥）
│   ├── app.py                 ← FastAPI 入口
│   ├── config.py              ← 配置加载
│   ├── eduagent.db            ← 本地开发数据库
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
├── data/
│   ├── chroma_db/             ← 向量库
│   ├── knowledge/             ← 知识库（131 文件）
│   ├── generated_resources/   ← 生成资源
│   └── sql/                   ← 数据库初始化脚本
├── docker/judge/              ← 判题沙箱 Dockerfile
└── scripts/                   ← 开发脚本（PowerShell）
```

## 必须修改项

1. **清理敏感信息** — `.env` 中的真实 API Key 必须替换为占位符
2. **清理临时文件** — 39GB 日志、缓存、IDE 配置、node_modules
3. **创建生产 docker-compose** — 添加 healthcheck、restart policy、卷挂载
4. **优化 nginx.conf** — 添加 gzip、缓存、SSE 超时、资源下载代理
5. **创建 Windows 部署脚本** — install/start/stop/restart/health/reset/logs
6. **预下载嵌入模型** — 避免首次启动联网
7. **创建发布脚本** — 自动生成源码包和安装运行包
8. **删除误放文件** — `frontend/src/eduagent.db`、`stickynotes/`

## 可选优化项

1. Python 依赖锁定（生成 requirements.lock）
2. Docker 镜像体积优化（multi-stage、alpine）
3. 前端构建优化（npm ci 替代 npm install）
4. 添加 CI/CD 配置
5. 添加 Docker Compose profiles（judge 服务）

## 不应修改的业务模块

1. `backend/agents/` — 5 个 Agent 实现
2. `backend/services/` — 业务服务层
3. `backend/api/` — API 路由
4. `backend/rag/` — RAG 实现
5. `backend/safety/` — 内容安全过滤
6. `frontend/src/` — 前端源码
7. `data/knowledge/` — 知识库
8. `data/sql/` — 数据库初始化脚本
