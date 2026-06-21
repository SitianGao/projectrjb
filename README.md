# EduAgent - 个性化学习多智能体系统

> 第15届软件杯 A3 — 基于大模型的个性化学习资源生成与学习多智能体系统

## 项目简介

本项目构建基于大模型和多智能体协同的个性化学习资源智能体平台，实现学生画像分析、学习路径规划、资源精准推荐和智能学习辅导。

## 技术栈

- **大模型**：讯飞星火 Spark 4.0
- **后端**：FastAPI + LangGraph
- **前端**：React + Ant Design + Vercel AI SDK
- **向量库**：ChromaDB
- **部署**：Docker Compose

## 快速启动

```powershell
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File scripts/start-all.ps1
```

默认地址：

- 前端：`http://localhost:5173`
- 后端 Swagger：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/health`

Docker Compose：

```powershell
docker compose up --build
```

Compose 前端地址为 `http://localhost:3000`，后端仍为 `http://localhost:8000`。

## 项目文档

- [赛题原文](docs/contestproblem.md)
- [需求分析](docs/requirement.md)
- [系统设计](docs/design.md)
- [项目准备指南](docs/prepare.md)
- [GitHub 协作规范](docs/github-workflow.md)
- [测试计划](docs/test_plan.md)

## 团队

- 队长：后端 + Agent 编排 + 集成
- 队员A：前端开发
- 队员B：AI/RAG + 知识库 + 安全

## 开源致谢

本项目使用了以下开源项目，感谢所有贡献者：

| 依赖 | 协议 |
|------|------|
| FastAPI | MIT |
| LangChain / LangGraph | MIT |
| ChromaDB | Apache 2.0 |
| React / Vite | MIT |
| Ant Design | MIT |
| Vercel AI SDK | Apache 2.0 |
| sentence-transformers | Apache 2.0 |
