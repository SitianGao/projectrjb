# 学习路径数据真实性审计报告

## 1. 截图页面定位

- 路由：`/course/:courseId/learn/:taskId`
- 页面：`frontend/src/pages/StudyHomePage.jsx`
- 全局布局：`frontend/src/App.jsx`
- 任务目录：`frontend/src/components/CourseTaskSidebar.jsx`
- 学习内容：`frontend/src/components/LearningContentPanel.jsx`
- AI 导师：`frontend/src/components/AITutorPanel.jsx`

## 2. 修改前的数据来源

截图内容是混合来源，不是一次真实 PlannerAgent 生成：

1. 课程、阶段标题、目标和 Seed 任务来自 `backend/scripts/init_demo_course.py`，已存入 SQLite。
2. `frontend/src/utils/courseLearning.js` 曾把阶段任务再次拼成固定的五类展示槽位。
3. `StudyHomePage.jsx` 曾按数组下标切换任务，并用前端延时模拟完成。
4. 旧 `learning_paths.stages` 是 JSON 快照，没有独立阶段、任务记录。

## 3. 固定数据与缓存审计

- 主学习页已不再导入 `buildStageLearningTasks`，也不再维护 `taskOverrides`。
- 完成任务不再使用 `setTimeout` 或本地 React 状态伪造。
- 学习路径和任务状态不写入 `localStorage`、`sessionStorage` 或 IndexedDB。
- `localStorage` 只用于认证令牌等会话信息。
- `frontend/src/mock/learningPathData.js` 仍供旧展示组件的标签配置使用，但不参与主演示学习执行链路。
- Seed 数据允许保留，但必须在数据库中标记 `generation_source=seed`。

## 4. 最终数据链

日常读取：

`StudyHomePage`
→ `frontend/src/api/courseLearning.js`
→ `GET /api/courses/{courseId}/learn/{taskId}`
→ `backend/api/course_learning_api.py`
→ `CourseLearningService`
→ `LearningPath + LearningStage + LearningTask`
→ SQLite

首次生成：

`useInitializeCourseLearning`
→ 真实 SSE `/api/courses/{courseId}/initialize/stream`
→ `ProfileAgent.build_profile_v2`
→ 保存画像版本
→ `PlannerAgent.generate_plan_v2`
→ 事务保存路径、阶段和任务
→ `ResourceAgent.prepare_stage_resources`
→ 返回真实 Agent 事件

## 5. 新增和调整的 API

- `POST /api/courses/{courseId}/initialize/stream`
- `GET /api/courses/{courseId}/learning-path`
- `GET /api/courses/{courseId}/learn`
- `GET /api/courses/{courseId}/learn/{taskId}`
- `POST /api/courses/{courseId}/tasks/{taskId}/complete`
- `GET /api/courses/{courseId}/learning-path/generation`

所有课程学习接口先校验登录用户，再以 `user_id + course_id + student_id` 查询当前有效路径。

## 6. 数据库调整

`users` 新增：

- `is_demo`

`learning_paths` 新增：

- `user_id`
- `course_id`
- `current_stage_id`
- `estimated_days`
- `generation_source`
- `generated_by`
- `provider`
- `model`
- `agent_run_id`
- `profile_version`
- `fallback_used`
- `fallback_type`
- `generated_at`

新增表：

- `learning_stages`
- `learning_tasks`
- `agent_runs`

路径、阶段和任务在同一事务中保存；任一环节失败会回滚。旧 `stages` JSON 只保留为兼容快照。

## 7. 进度和任务恢复

- 当前阶段由 `learning_paths.current_stage_id` 恢复。
- 当前任务由真实任务状态、前置任务和阶段顺序计算。
- 完成接口幂等；重复提交不会重复计数。
- 后端统一计算任务解锁、阶段进度和总路径进度。
- 前端完成后使用响应中的下一任务更新路由。
- 浏览器已验证完成任务后从 `1/6` 变为 `2/6`，进入下一任务，刷新后仍保持。

## 8. 类型显示

内部 `task_type` 保持不变，后端统一返回中文 `type_label`：

- `objective` / `goal`：学习目标
- `document`：核心讲义
- `mindmap`：概念图解
- `exercise`：知识检查
- `assessment`：阶段测评
- `code`：代码实操
- `ppt`：教学课件
- `interactive_classroom`：AI 互动课堂

## 9. 生成来源与 Agent 日志

路径页“查看生成依据”展示：

- 路径来源
- 生成 Agent
- Provider / Model
- 画像版本
- 路径版本
- 是否规则降级
- 生成时间

来源取值：`agent`、`seed`、`manual`、`rule_fallback`、`legacy`。旧数据不猜测为 Agent。

`agent_runs` 记录 run、Agent、用户、课程、阶段、任务、Provider、Model、状态、耗时、fallback、知识命中和错误码，不记录密钥或完整敏感 Prompt。

## 10. SSE 真实性

前端已移除本地定时器模拟的 Agent 步骤。后端在真实执行点发送：

- `workflow_started`
- `agent_started`
- `agent_completed`
- `agent_failed`
- `path_saved`
- `resource_job_created`
- `workflow_completed`

## 11. 演示身份和数据

- `user_id/username`：`demo_student`
- `display_name`：`演示同学`
- `is_demo`：`true`
- `course_id`：`ai_deep_learning_demo`
- `course_name`：`人工智能与深度学习`

`student`、`student123` 和其他课程不能读取该课程路径。切换到无路径课程时返回空/404，不复用上一课程任务。

初始化与重置：

```powershell
python backend/scripts/seed_demo_student.py
python backend/scripts/reset_demo_student.py
```

两个脚本均可重复执行。重置后主演示起点为阶段二核心讲义，阶段进度 `1/6`。

## 12. 严格模式与星火验证

比赛录制配置建议：

```env
LLM_PRIMARY=spark
SPARK_ENABLED=true
SPARK_API_PASSWORD=<比赛环境密钥>
LLM_STRICT_MODE=true
RAG_STRICT_MODE=true
RESOURCE_STRICT_MODE=true
```

当前本机 `.env` 的 `SPARK_API_PASSWORD` 为空且 `LLM_STRICT_MODE=false`，因此当前 Seed 页面不能宣称是本次星火实时生成。

真实调用成功的判据：

1. SSE 中 PlannerAgent `agent_completed` 的 `provider=spark` 且有真实 `model`、`run_id`、`duration_ms`。
2. `agent_runs` 对应记录为 `completed`。
3. 路径 `generation_source=agent`、`provider=spark`、`fallback_used=false`。
4. “查看生成依据”显示相同信息。

严格模式下调用失败会发送 `agent_failed` 并返回可重试错误，不会切换模型或规则模板伪装成功。

## 13. 动态路径验证

`test/test_learning_path_truth.py` 覆盖：

- 初级图像分类画像包含机器学习基础、梯度下降、神经网络、CNN 和项目实践。
- 已掌握基础的高级画像缩短基础阶段。
- NLP / 文本分类目标生成明显不同的阶段和知识点。
- 比较阶段标题、学习目标、任务类型等内容，不只比较 path_id。

## 14. 验证结果

- `pytest test/test_learning_path_truth.py -q`：8 passed
- 相关前端文件 ESLint：通过
- `npm run build`：通过
- 浏览器：登录、路径页、生成依据、继续学习、完成任务、下一任务和刷新持久化均通过

