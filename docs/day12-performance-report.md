# Day12 性能与稳定性记录

日期：2026-06-19  
负责人：队长

## 目标

让后端达到连续使用水平：SSE 尽快返回首帧、资源生成任务有可解释进度、LLM 调用有明确超时重试、并发资源生成不会串任务，并关闭后端 P0/P1 问题。

## 后端优化记录

| 项目 | 处理结果 | 验收证据 |
| --- | --- | --- |
| SSE 首字延迟 | 画像、路径、辅导接口将 `start` 事件前移，避免等 DB/LLM 后才给前端反馈 | `test_day12_performance.py::test_planner_sse_emits_start_before_profile_lookup` |
| 异步任务进度 | 资源任务增加 `phase`、`progress_history`、`started_at`、`finished_at`、`duration_ms` | `test_day12_performance.py::test_resource_task_reports_stage_progress` |
| 并发资源生成 | `TaskService` 增加线程锁，任务读写返回副本，避免并发状态串扰 | `test_day12_performance.py::test_concurrent_resource_generation_tasks_do_not_interfere` |
| LLM 超时重试 | Spark HTTP 非 2xx 会触发重试；重试失败后切 DeepSeek；HTTP 连接/读写/连接池超时明确化 | `test_day12_performance.py::test_llm_client_retries_spark_and_falls_back_to_deepseek` |

## 性能测试记录

本地自动化执行命令：

```powershell
pytest test/test_api_contract.py test/test_api_errors.py test/test_day11_e2e.py test/test_day12_performance.py -q -p no:cacheprovider
```

结果：

```text
25 passed
```

覆盖指标：

| 指标 | 目标 | 自动化结论 |
| --- | --- | --- |
| SSE 首事件 | 首个事件为 `start` | 已通过 |
| 异步任务进度 | 至少包含 queued/started/generating/done 等阶段 | 已通过 |
| 并发资源生成 | 5 个任务 ID 唯一、结果不串学生/主题 | 已通过 |
| LLM 重试 | Spark 失败后重试并切备用模型 | 已通过 |

## P0 / P1 后端问题关闭记录

| 编号 | 等级 | 问题 | 状态 | 证据 |
| --- | --- | --- | --- | --- |
| BE-P0-001 | P0 | 接口失败缺少 `code/message` | 已关闭 | Day10 `test_api_errors.py` |
| BE-P0-002 | P0 | 固定学生主流程不能连续跑通 | 已关闭 | Day11 `test_day11_e2e.py` |
| BE-P0-003 | P0 | 资源并发生成可能串任务状态 | 已关闭 | Day12 并发测试 + `TaskService` 加锁 |
| BE-P1-001 | P1 | 资源生成任务进度只有 20 -> 100，页面进度跳变明显 | 已关闭 | `phase` + `progress_history` |
| BE-P1-002 | P1 | SSE 入口可能在慢操作后才首帧反馈 | 已关闭 | `start` 事件前移 |
| BE-P1-003 | P1 | LLM HTTP 错误未明确进入重试路径 | 已关闭 | `response.raise_for_status()` + 重试测试 |

## 对接记录

- 队长 -> 队员A：资源任务状态可读取 `phase` 和 `progress_history`，页面可按阶段显示“准备/生成/保存/整理/完成”。
- 队长 -> 队员A：SSE 第一条事件稳定为 `start`，页面收到后应立刻进入加载/流式状态。
- 队长 -> 队员B：LLM Spark 超时或 HTTP 错误会重试，全部失败后切 DeepSeek；Agent 层不需要自己重复实现重试。
- 全员确认：截至 Day12，后端 P0 清零；剩余前端截图、页面兼容性和 RAG 质量问题由对应负责人继续记录。

## 手工补充验收

自动化已覆盖后端稳定性。前端兼容性截图由队员A补：

- 1366x768 首页、画像、路径、资源、问答、评估截图
- 手机宽度核心页面截图
- 资源生成进度条截图
- SSE 问答首帧和流式过程截图
