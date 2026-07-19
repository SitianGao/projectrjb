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

## 最终学习流程

平台的日常主流程为：

`学习首页 → 学习路径 → 当前任务 → StageResourcePage 直接学习`

`ResourceAgent` 隐藏在任务背后，按课程、阶段、任务和学生画像准备内容。“我的学习资料”只负责搜索、筛选、收藏、回看和继续学习；路径之外的自由生成统一进入“AI 学习工作台”。

主导航为：学习首页、学习路径、AI 学习助手、学习评估、我的学习资料。旧 `/generating` 与 `/resources/generate` 路由仍可访问，但会跳转到 AI 学习工作台。

## 比赛演示账号

- `demo_student / demo123`：稳定演示账号，已有课程、路径、学习记录和预置资料。用于展示任务学习、错题、评估、专项任务和资料回看。
- `demo_new`：录制前通过注册页创建的新账号。用于现场完成画像、生成路径、进入任务，展示实时 RAG + ResourceAgent 过程和自动归档。建议每次完整演示使用新的用户名，保证流程从空状态开始。

资源生成入口全部复用同一个 `ResourceService`：任务型场景进入 `generate_contextual_resource()`，路径外的 AI 学习工作台进入该服务的 `generate_resources()`。同一用户、任务、资源类型、难度和生成版本默认复用已有结果，只有明确“重新生成”时创建关联当前资源的新变体。

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
