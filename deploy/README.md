# EduAgent 部署指南

## 中国软件杯 A3 - 基于大模型的个性化资源生成与学习多智能体系统

---

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 64位 |
| Docker | Docker Desktop 4.0+ |
| 内存 | 推荐 16GB（最低 8GB） |
| 磁盘 | 10GB 可用空间 |
| 网络 | 需要联网（首次下载镜像/模型） |

---

## 快速开始

### 方式一：使用预构建镜像（推荐）

1. **安装 Docker Desktop**
   - 下载：https://www.docker.com/products/docker-desktop/
   - 安装并启动

2. **运行安装脚本**
   ```
   双击 scripts\install.bat
   ```

3. **配置 API Key**
   - 编辑 `deploy\.env` 文件
   - 填入讯飞星火 API 凭证

4. **启动系统**
   ```
   双击 scripts\start.bat
   ```

5. **访问系统**
   - 前端：http://localhost:3000
   - API 文档：http://localhost:8000/docs
   - 演示账号：`demo_student` / `demo123`

### 方式二：从源码构建

1. **确保 Docker Desktop 运行**

2. **进入 deploy 目录**
   ```
   cd deploy
   ```

3. **构建镜像**
   ```
   docker compose -f docker-compose.prod.yml build
   ```

4. **启动系统**
   ```
   docker compose -f docker-compose.prod.yml up -d
   ```

---

## 管理脚本

| 脚本 | 功能 |
|------|------|
| `scripts\install.bat` | 安装（加载镜像、创建卷） |
| `scripts\start.bat` | 启动系统 |
| `scripts\stop.bat` | 停止系统 |
| `scripts\restart.bat` | 重启系统 |
| `scripts\health-check.bat` | 健康检查 |
| `scripts\reset-demo.bat` | 重置演示数据 |
| `scripts\view-logs.bat` | 查看日志 |
| `scripts\uninstall.bat` | 卸载系统 |

---

## 配置说明

编辑 `deploy\.env` 文件：

```ini
# 讯飞星火配置（必填）
SPARK_API_PASSWORD=your_api_password
SPARK_APP_ID=your_app_id
SPARK_API_SECRET=your_api_secret
SPARK_API_KEY=your_api_key

# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

详细配置说明见 `config\CONFIGURATION.md`。

---

## 无 API Key 演示

如果不配置 API Key，系统支持以下功能：

- ✅ 知识库浏览
- ✅ 演示数据展示
- ✅ 学习路径查看
- ✅ 评估报告（规则引擎模式）
- ⚠️ Agent 对话降级为模板回复
- ⚠️ 资源生成降级为静态资源

---

## 目录结构

```
deploy/
├── docker-compose.prod.yml    # 生产环境 Compose 配置
├── Dockerfile.backend          # 后端镜像构建
├── Dockerfile.frontend         # 前端镜像构建
├── nginx.conf                  # Nginx 配置
├── .env                        # 运行时配置（从 .env.example 复制）
├── config/
│   ├── .env.example           # 配置模板
│   └── CONFIGURATION.md       # 配置说明
├── images/                     # 预构建镜像（.tar 文件）
│   ├── eduagent-backend.tar
│   └── eduagent-frontend.tar
└── scripts/
    ├── install.bat            # 安装脚本
    ├── start.bat              # 启动脚本
    ├── stop.bat               # 停止脚本
    ├── restart.bat            # 重启脚本
    ├── health-check.bat       # 健康检查
    ├── reset-demo.bat         # 重置演示数据
    ├── view-logs.bat          # 查看日志
    └── uninstall.bat          # 卸载脚本
```

---

## 常见问题

### Q: 启动后页面空白？
A: 后端首次启动需要初始化数据库和 RAG，请等待 1-2 分钟后刷新。

### Q: 如何查看后端日志？
A: 运行 `scripts\view-logs.bat backend`

### Q: 如何重置演示数据？
A: 运行 `scripts\reset-demo.bat`

### Q: 端口被占用？
A: 编辑 `.env` 文件修改 `BACKEND_PORT` 和 `FRONTEND_PORT`。

### Q: Docker 镜像下载慢？
A: 配置 Docker 镜像加速器（设置 → Docker Engine → registry-mirrors）。

---

## 技术架构

```
浏览器 (http://localhost:3000)
    │
    ▼
Nginx (前端静态文件 + API 反向代理)
    │
    ├── /api/* ──→ FastAPI 后端 (port 8000)
    │                  │
    │                  ├── ProfileAgent   (学生画像)
    │                  ├── PlannerAgent   (学习规划)
    │                  ├── ResourceAgent  (资源生成)
    │                  ├── TutorAgent     (智能辅导)
    │                  ├── EvaluateAgent  (评估诊断)
    │                  │
    │                  ├── SQLite         (数据持久化)
    │                  ├── ChromaDB       (向量检索)
    │                  └── 讯飞星火 API   (大模型)
    │
    └── /* ──→ 静态文件 (React SPA)
```

---

## 许可证

本项目为"中国软件杯"A3 赛题参赛作品。
