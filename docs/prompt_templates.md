# Prompt 模板收敛文档（Day 11 交付物）

> 队员B | 2026-06-19 | 对齐 design.md Day 11

## 收敛目标

将 5 个 Agent 的 System Prompt 收敛为统一的结构化模板，消除各 Agent 之间 Prompts 风格不一致的问题。

收敛前的问题：
- ProfileAgent/PlannerAgent 各有独立 prompt 风格，规则密度不均
- ResourceAgent/TutorAgent 缺少标准化的输出格式约束
- 防幻觉规则仅 ProfileAgent 有 5 条完整规则，其余 Agent 仅 3 条

收敛后的统一结构见下方。

---

## 统一定义模板结构

每个 Agent 的 System Prompt 必须包含以下 **5 个区块**（顺序固定）：

```
1. 角色定义     — 一句话定义 Agent 身份和职责
2. 工作任务     — 详细工作要求和行为规范（2-5 条）
3. 输出格式     — 严格 JSON schema 定义
4. 防幻觉约束   — 5-6 条通用规则（禁止编造、诚实标注不确定性、不生成不安全内容等）
5. 降级/边界    — 输入无效时的处理策略
```

---

## 各 Agent 的收敛后 Prompt

### 1. ProfileAgent (`profile_agent.py:26-107`)

| 区块 | 内容 | 行数 |
|------|------|------|
| 角色定义 | "你是一个学生画像构建智能体" | 1 行 |
| 工作任务 | 6 维度提取 + 增量更新规则 + 置信度标注 + 追问策略 | ~50 行 |
| 输出格式 | `{profile, completeness, confidence, sources, next_questions}` | 12 行 JSON |
| 防幻觉约束 | 5 条规则 | 5 行 |
| 降级/边界 | 内容安全过滤 → `_keyword_fallback()` | 方法级 |

**收敛前**：防御规则仅 3 条非编号建议混在工作要求中。
**收敛后**：独立 `## 防幻觉约束` 区块，5 条编号规则，强调"不猜测未提及的信息"和"诚实标注置信度"。

### 2. PlannerAgent (`planner_agent.py`)

| 区块 | 内容 |
|------|------|
| 角色定义 | "你是一个学习路径规划智能体" |
| 工作任务 | 阶段划分 + 任务粒度 + 时间估计 + 资源匹配 |
| 输出格式 | `{stages: [{stage_id, name, estimated_days, tasks}]}` |
| 防幻觉约束 | **6 条编号规则**：不编造课程 → 时间切实可行 → 拒绝无关领域 → 不生成不安全内容 → 标注不确定性 → 诚实告知知识范围 |

**收敛前**：防幻觉区仅 3 个 bullet point，无编号。
**收敛后**：6 条编号规则，每条以 `不` 或 `只` 开头，简洁有力。

### 3. ResourceAgent (`resource_agent.py`)

| 区块 | 内容 |
|------|------|
| 角色定义 | "你是一个学习资源生成智能体" |
| 工作任务 | 按类型生成资源 + 难度适配 + 知识上下文注入 |
| 输出格式 | `{resources: [{type, title, topic, difficulty, content}]}` |
| 防幻觉约束 | **6 条编号规则**：只生成学习资源 → 不编造不存在的内容 → 不生成不安全/违规内容 → 资源引用须核验 → 不在请求领域外生成 → 使用专业知识确保准确 |

**收敛前**：无独立防幻觉区块，仅在工作要求中混入 2 条建议。
**收敛后**：独立 `## 防幻觉约束` 区块，与前两个 Agent 结构化一致。

### 4. TutorAgent (`tutor_agent.py:63-85`)

| 区块 | 内容 |
|------|------|
| 角色定义 | "你是智能辅导问答智能体" |
| 工作任务 | 4 条：认知水平适配 + 后续问题引导 + 非学术引导 + RAG 优先 |
| 输出格式 | `{answer, explanation_style, references, diagrams}` |
| 防幻觉约束 | **5 条编号规则**：只回答确定内容 → 公式/定理务必核实 → 超出范围诚实告知 → 不生成不安全内容 → RAG 无依据时的标准回复 |

**收敛前**：已是 5 条规则，但缺少独立的输出格式区块。
**收敛后**：增加 `## 输出格式` 区块，5 条防幻觉规则保持不变（本身质量高）。

### 5. EvaluateAgent (`evaluate_agent.py`)

| 区块 | 内容 |
|------|------|
| 角色定义 | "你是一个学习评估与反馈智能体" |
| 工作任务 | 成绩分析 + 维度评估 + 复习计划 + 建议生成 |
| 输出格式 | `{overall_score, dimensions, review_plan, suggestions}` |
| 防幻觉约束 | **6 条编号规则**：严禁编造成绩 → 仅基于提供的 records → 诚实标注不确定性 → 不生成不安全内容 → 遗忘曲线为辅助依据 → 避免过度推断 |

**收敛前**：防御规则仅 3 个 bullet point。
**收敛后**：6 条编号规则，其中新增"遗忘曲线为辅助依据"特异性约束。

---

## 防幻觉规则标准化对照表

以下 6 条规则是所有 Agent 共享的基线要求：

| # | 规则 | Profile | Planner | Resource | Tutor | Evaluate |
|---|------|:---:|:---:|:---:|:---:|:---:|
| 1 | 仅基于提供的信息/学生实际表述，不猜测 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 | 诚实标注不确定性/置信度 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3 | 不编造不存在的内容/数据/成绩 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4 | 不生成违规、敏感或不安全的内容 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 5 | 超出知识范围时诚实告知 | — | ✅ | ✅ | ✅ | ✅ |
| 6 | 遵守输出格式（严格 JSON） | ✅ | ✅ | ✅ | ✅ | ✅ |

特异性规则（仅特定 Agent）：
- **ProfileAgent #5**: 若学生输入超出学习范围，礼貌引导回画像构建
- **ResourceAgent #5**: 不在请求领域外生成资源
- **ResourceAgent #6**: 使用专业知识确保资源内容准确
- **EvaluateAgent #5**: 遗忘曲线为辅助依据，不替代实际评估
- **TutorAgent #5**: RAG 无依据 → 标准无资料回复模板

---

## 输出格式标准化

所有 5 个 Agent 的输出均收敛为 **JSON 字典**（非字符串），结构如下：

| Agent | 返回结构 | 外层包装 |
|-------|---------|---------|
| ProfileAgent | `{student_id, profile, completeness, confidence, sources, next_questions}` | Dict |
| PlannerAgent | `{stages: [...], total_estimated_days, risk_warnings, adaptation_notes}` | Dict |
| ResourceAgent | `{resources: [{type, title, topic, difficulty, content}]}` | Dict |
| TutorAgent | `{answer, explanation_style, references, diagrams}` | JSON string (SSE 兼容) |
| EvaluateAgent | `{overall_score, progress, efficiency, dimensions, review_plan, suggestions}` | Dict |

---

## 安全 Prompt 统一注入点

所有面向用户的 Agent（TutorAgent, ProfileAgent）都在 `方法入口` 统一调用：

```python
from backend.safety.content_filter import check_safety
filter_result = check_safety(user_input, context="agent_name")
if not filter_result["safe"]:
    return block_response(filter_result)
```

PlannerAgent / ResourceAgent / EvaluateAgent 无需在方法入口做安全过滤（其输入来自系统内部/编排器，非直接用户输入），但其 System Prompt 中的防幻觉规则第 4 条均包含"不生成不安全内容"约束。
