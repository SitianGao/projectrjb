"""
API 路由层 —— 处理 HTTP 请求/响应。

==== 接口全景图（来源: docs/design.md §6.1 接口总览）====

  方法     路径                             用途              响应方式      对应文件
 ───────────────────────────────────────────────────────────────────────────────────
  GET     /                                健康检查           JSON         app.py
  POST    /api/profile/chat                对话式画像构建      SSE 流式     profile_api.py
  GET     /api/profile/{student_id}        获取学生画像        JSON         profile_api.py
  PUT     /api/profile/{student_id}        更新画像            JSON         profile_api.py
  POST    /api/planner/generate            生成学习路径        SSE 流式     planner_api.py
  GET     /api/planner/{student_id}        获取学习路径        JSON         planner_api.py
  POST    /api/resource/generate           生成学习资源        异步任务      resource_api.py
  GET     /api/resource/{resource_id}      获取资源详情        JSON         resource_api.py
  GET     /api/resource/list?student_id=   资源列表            JSON         resource_api.py
  POST    /api/tutor/chat                  智能辅导问答        SSE 流式     tutor_api.py
  POST    /api/evaluate/start              开始学习评估        JSON         evaluate_api.py
  GET     /api/evaluate/report/{student_id} 获取评估报告       JSON         evaluate_api.py
  POST    /api/evaluate/record             提交学习记录        JSON         evaluate_api.py
  GET     /api/task/{task_id}/status       查询异步任务进度     JSON         task_api.py

==== 统一规范（来源: docs/design.md §6.2 统一规范）====

  - 所有接口前缀 /api/
  - 流式接口: Content-Type: text/event-stream（SSE 事件格式见 design.md §10.4.2）
  - 异步任务: 返回 task_id，前端轮询 /api/task/{id}/status
  - 成功响应: {"success": true, "data": {}, "message": "ok"}
  - 错误响应: {"success": false, "error": true, "code": "ERROR_CODE", "message": "描述"}
  - 字段命名: snake_case
  - 时间格式: ISO 8601（2026-06-07T10:30:00+08:00）
  - 学生 ID: UUID 字符串
  - 任务 ID: "task_" 前缀

==== 代码分层（API → Service → Agent/DB）====

  路由文件 (api/)     →  业务逻辑 (services/)       →  数据/Agent 层
  ─────────────────────────────────────────────────────────────────
  profile_api.py      →  profile_service.py         →  ProfileAgent + models.Student
  planner_api.py      →  planner_service.py          →  PlannerAgent + models.LearningPath
  resource_api.py     →  resource_service.py         →  ResourceAgent + models.Resource
  tutor_api.py        →  tutor_service.py            →  TutorAgent
  evaluate_api.py     →  evaluate_service.py         →  EvaluateAgent + models.LearningRecord
  task_api.py         →  task_manager.py             →  utils/task_manager.py
"""
