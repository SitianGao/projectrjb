# EduAgent 配置说明

## 快速配置

1. 复制 `deploy/config/.env.example` 为 `deploy/.env`
2. 填入你的讯飞星火 API 凭证
3. 运行 `deploy/scripts/start.bat`

## 配置项详解

### LLM 模型配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_PRIMARY` | 主模型选择 | `spark` |
| `SPARK_ENABLED` | 是否启用星火 | `true` |
| `SPARK_API_PASSWORD` | 星火 API 密码 | 必填 |
| `SPARK_MODEL` | 模型版本 | `4.0Ultra` |
| `SPARK_APP_ID` | 应用 ID | 可选 |
| `SPARK_API_SECRET` | API Secret | 可选 |
| `SPARK_API_KEY` | API Key | 可选 |
| `DEEPSEEK_API_KEY` | DeepSeek 备用密钥 | 可选 |

### 端口配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BACKEND_PORT` | 后端 API 端口 | `8000` |
| `FRONTEND_PORT` | 前端访问端口 | `3000` |

### RAG 配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `EMBEDDING_MODEL` | 嵌入模型 | `paraphrase-multilingual-MiniLM-L12-v2` |
| `RAG_STRICT_MODE` | RAG 严格模式 | `true` |
| `RESOURCE_STRICT_MODE` | 资源严格模式 | `true` |

### 演示模式

系统内置演示账号：
- 用户名：`demo_student`
- 密码：`demo123`

演示课程"人工智能与深度学习"会在首次启动时自动初始化。

### 无 API Key 演示

如果不配置 API Key，系统会：
1. Agent 功能降级为规则引擎模式
2. RAG 检索仍正常工作
3. 知识库浏览正常
4. 演示数据完整可用
