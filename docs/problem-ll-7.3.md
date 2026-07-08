# 数据库缺口 & 前后端配合问题清单

> 整理日期：2026-07-03
> 范围：数据库模型、API 路由、前端页面接入情况

---

## 一、数据库缺少的内容

### 1. 缺少用户认证表 (`users`)

**现状**：前端 `AuthContext` 使用硬编码 `MOCK_USERS` 数组（[AuthContext.jsx:8-11](../frontend/src/contexts/AuthContext.jsx#L8-L11)），登录/注册均为模拟逻辑。`students` 表存在但不承载认证功能。

**需要新增字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| username | VARCHAR(100) UNIQUE | 用户名 |
| email | VARCHAR(200) | 邮箱 |
| password_hash | VARCHAR(255) | 密码哈希 |
| role | VARCHAR(20) | student / admin |
| is_active | BOOLEAN | 是否激活 |
| last_login_at | DATETIME | 最后登录时间 |
| created_at / updated_at | DATETIME | 时间戳 |

**需要新增的后端 API**：
- `POST /api/auth/register` — 注册
- `POST /api/auth/login` — 登录（返回 token）
- `POST /api/auth/forgot-password` — 忘记密码
- `GET /api/auth/me` — 获取当前用户信息

---

### 2. 缺少辅导会话持久化表

**现状**：`TutorService` 使用内存字典 `_sessions` 和 `_messages`（[tutor_service.py:27-28](../backend/services/tutor_service.py#L27-L28)），服务重启后全部丢失。

**需要新增**：

#### `tutor_sessions` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| student_id | VARCHAR(36) FK | 关联学生 |
| title | VARCHAR(200) | 会话标题 |
| explanation_style | VARCHAR(20) | auto / analogy / formula / visual / story |
| message_count | INTEGER | 消息数 |
| created_at / updated_at | DATETIME | 时间戳 |

#### `tutor_messages` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| session_id | VARCHAR(36) FK | 关联会话 |
| role | VARCHAR(20) | user / assistant |
| content | TEXT | 消息内容 |
| references | TEXT | RAG 引用（JSON） |
| created_at | DATETIME | 时间戳 |

---

### 3. 缺少任务持久化表

**现状**：`TaskService` 和 `TaskManager` 均使用内存字典（[task_service.py:14](../backend/services/task_service.py#L14) / [task_manager.py:29](../backend/utils/task_manager.py#L29)），服务重启后异步任务状态全部丢失。

**需要新增**：

#### `tasks` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | task_xxx |
| type | VARCHAR(30) | resource_generate / evaluate |
| student_id | VARCHAR(36) FK | 关联学生 |
| status | VARCHAR(20) | pending / running / done / failed |
| progress | REAL | 0.0 - 1.0 |
| message | VARCHAR(200) | 当前阶段描述 |
| result | TEXT | 结果数据（JSON） |
| error | TEXT | 错误信息（JSON） |
| created_at / updated_at | DATETIME | 时间戳 |

---

### 4. 缺少知识库管理表

**现状**：`data/knowledge/` 中有知识文件，但无数据库表追踪加载状态。

**需要新增**：

#### `knowledge_documents` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| file_path | VARCHAR(500) | 相对路径 |
| file_name | VARCHAR(200) | 文件名 |
| category | VARCHAR(100) | 分类（知识点 / 习题 / 其他） |
| chunk_count | INTEGER | 切片数量 |
| file_hash | VARCHAR(64) | 文件哈希（检测变更） |
| is_indexed | BOOLEAN | 是否已向量化 |
| indexed_at | DATETIME | 索引时间 |
| created_at | DATETIME | 时间戳 |

---

### 5. 缺少系统配置表

**现状**：没有可通过 API 修改系统配置的数据库表，所有配置在 `.env` 文件中。

**需要新增**：

#### `system_configs` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| config_key | VARCHAR(100) UNIQUE | 配置键 |
| config_value | TEXT | 配置值 |
| description | VARCHAR(200) | 说明 |
| updated_by | VARCHAR(36) | 修改人 |
| updated_at | DATETIME | 修改时间 |

---

### 6. 缺少反馈/评分表

**现状**：
- `POST /api/resource/{id}/bookmark` 是桩代码，返回固定值（[resource_api.py:144-150](../backend/api/resource_api.py#L144-L150)）
- 辅导回答无点赞/点踩机制
- 无用户反馈收集

**需要新增**：

#### `resource_bookmarks` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| student_id | VARCHAR(36) FK | 关联学生 |
| resource_id | VARCHAR(36) FK | 关联资源 |
| created_at | DATETIME | 收藏时间 |

#### `feedbacks` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| student_id | VARCHAR(36) FK | 关联学生 |
| target_type | VARCHAR(30) | resource / tutor_answer |
| target_id | VARCHAR(36) | 目标 ID |
| rating | INTEGER | 评分 1-5 |
| content | TEXT | 反馈文本 |
| created_at | DATETIME | 时间戳 |

---

### 7. 缺少通知表

**现状**：前端 `NotificationCenter` 使用 `MOCK_NOTIFICATIONS` 硬编码数据（[NotificationCenter.jsx:15](../frontend/src/components/NotificationCenter.jsx#L15)）。

**需要新增**：

#### `notifications` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| student_id | VARCHAR(36) FK | 关联学生 |
| type | VARCHAR(30) | review_remind / path_update / system |
| title | VARCHAR(200) | 通知标题 |
| content | TEXT | 通知内容 |
| is_read | BOOLEAN | 是否已读 |
| created_at | DATETIME | 时间戳 |

---

### 8. 现有表的次要问题

| 表 | 问题 | 建议 |
|-----|------|------|
| `resources` | `path_id` 外键关联的路径被标记 superseded 后，资源成为孤儿 | 保留历史路径或允许 path_id 为 NULL |
| `student_profiles` | JSON 字段（weakness / interest / memory_strength）以 TEXT 存储，无应用层验证 | 在 Service 层加序列化/反序列化校验 |
| `learning_records` | `resource_id` 可为 NULL，有资源和无资源记录未区分 | 考虑按 action 类型规范化 |
| 所有表 | 无软删除机制（`deleted_at`） | 对关键表增加软删除字段 |

---

## 二、前端与应用层 API 需要配合的地方

### 🔴 P0：认证系统（Auth）

| 层级 | 当前状态 | 需要做什么 |
|------|----------|------------|
| **数据库** | 无 `users` 表 | 创建 users 表（见上文） |
| **后端** | 无 `/api/auth/*` 路由 | 创建 register / login / forgot-password / me 端点 |
| **前端** | `AuthContext` 硬编码 MOCK_USERS | 接入真实 API；LoginPage / RegisterPage / ForgotPasswordPage 调用真实接口 |

---

### 🔴 P0：TutorPage 路由缺失

- **后端**：辅导 API 已完整实现（[tutor_api.py](../backend/api/tutor_api.py)），包含 `/api/tutor/chat`（SSE）、`/api/tutor/sessions`、`/api/tutor/ask/stream` 等
- **前端**：`App.jsx` 中**没有 TutorPage 的路由和懒加载 import**，学生无法进入辅导页面
- **需要**：创建 `TutorPage.jsx` 并在 `App.jsx` 中新增 `/tutor` 路由

---

### 🔴 P0：EvaluatePage 路由缺失

- `EvaluatePage.jsx` **文件已存在**（[EvaluatePage.jsx](../frontend/src/pages/EvaluatePage.jsx)）
- 但 `App.jsx` **未导入且未挂载路由**
- **需要**：在 `App.jsx` 中新增 `/evaluate` 路由

---

### 🟡 P1：API 路径不匹配（3 处）

| 前端调用 | 实际后端路由 | 状态 |
|----------|-------------|------|
| `POST /api/evaluate/start/stream` | `POST /api/evaluate/generate/stream` | ❌ 不匹配 |
| `GET /api/evaluate/report/{id}/progress` | `GET /api/evaluate/progress/{student_id}` | ❌ 不匹配 |
| `GET /api/resources` | `GET /api/resource/list`（兼容前缀存在） | ✅ 已兼容 |

---

### 🟡 P1：桩代码接口（4 个）

| 接口 | 当前行为 | 需要做什么 |
|------|----------|------------|
| `POST /api/resource/{id}/bookmark` | 返回 `bookmarked: true`，无持久化 | 新增 `resource_bookmarks` 表，实现真实收藏/取消 |
| `POST /api/tutor/check` | 返回 "答案检查功能待 EvaluateAgent 接入" | 接入真实 EvaluateAgent 答案检查逻辑 |
| `GET /api/tutor/history/{session_id}` | 返回 `{"messages": []}` | 需从持久化存储读取（目前纯内存） |
| `POST /api/evaluate/generate` | 等同于 start_evaluation，与 SSE 版本行为不一致 | 需明确与 generate/stream 的关系 |

---

### 🟡 P1：Mock 降级普遍存在

以下页面大量依赖 `shouldUseMock()`（`VITE_USE_MOCK=true`），根据设计文档 Day 14 要求，技术冻结前需清理：

| 页面 | Mock 覆盖范围 |
|------|--------------|
| [ProfilePage.jsx](../frontend/src/pages/ProfilePage.jsx) | 画像、路径、统计数据 |
| [HomePage.jsx](../frontend/src/pages/HomePage.jsx) | 画像、评估、进度统计 |
| [ResourcePage.jsx](../frontend/src/pages/ResourcePage.jsx) | 资源生成、任务轮询 |
| [EvaluatePage.jsx](../frontend/src/pages/EvaluatePage.jsx) | 评估报告、进度统计 |
| [LearningPathPage.jsx](../frontend/src/pages/LearningPathPage.jsx) | 路径时间线、统计数据 |
| [NotificationCenter.jsx](../frontend/src/components/NotificationCenter.jsx) | 通知列表 |
| [ChatBox.jsx](../frontend/src/components/ChatBox.jsx) | 默认消息 |
| [ProfileCard.jsx](../frontend/src/components/ProfileCard.jsx) | 默认画像数据 |

---

### 🟢 P2：缺少管理员控制台

目前完全没有任何管理员界面。需要一个最小化控制台：

**后端需新增：**
- `GET /api/admin/stats` — 系统统计（用户数、资源数、会话数、RAG 文档数）
- `GET /api/admin/students` — 学生列表
- `GET /api/admin/knowledge` — 知识库文档列表 + 状态
- `POST /api/admin/knowledge/reindex` — 重新索引知识库
- `GET /api/admin/configs` / `PUT /api/admin/configs` — 系统配置管理
- `GET /api/admin/logs` — 最近日志

**前端需新增：**
- `AdminPage.jsx` — 管理面板页面
- 在 `App.jsx` 中新增 `/admin` 路由（仅 admin 角色可访问）

---

## 三、优先级汇总

| 优先级 | 项目 | 负责方 |
|--------|------|--------|
| **P0** | 创建 `users` 表 + `/api/auth/*` 接口 | 队长（后端 + 数据库） |
| **P0** | 前端 AuthContext 接入真实 API | 队员A（前端） |
| **P0** | 新增 TutorPage 路由和页面 | 队员A（前端） |
| **P0** | 新增 EvaluatePage 路由 | 队员A（前端） |
| **P0** | 修复 API 路径不匹配（evaluate 相关 2 处） | 队长 + 队员A |
| **P1** | tutor_sessions / messages 持久化到数据库 | 队长（数据库） |
| **P1** | tasks 状态持久化到数据库 | 队长（数据库） |
| **P1** | 清理前端 Mock 降级 | 队员A（前端） |
| **P2** | 新增 resource_bookmarks / notifications / feedbacks 表 | 队长（数据库） |
| **P2** | 构建最小管理员控制台（前端 + 后端） | 队长 + 队员A |
| **P2** | 新增 knowledge_documents / system_configs 表 | 队长（数据库） |
