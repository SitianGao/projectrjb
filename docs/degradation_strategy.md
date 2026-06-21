# 降级策略文档（Day 11 交付物）

> 队员B | 2026-06-19 | 对齐 design.md Day 11

## 1. 总则

系统中所有 AI 功能均遵循 **双重降级** 原则：

```
LLM 调用 → 失败/超时/输出非法 JSON → 规则化兜底 → 永远不返回空
```

每个 Agent 都具备独立的 `_rule_based_*()` 方法，保证 LLM 不可用时系统核心功能不中断。

---

## 2. 各 Agent 降级链路

### 2.1 ProfileAgent

| 环节 | 正常路径 | 降级路径 |
|------|---------|---------|
| LLM 调用 | `call_llm()` 流式返回 | 异常 → `_keyword_fallback()` |
| JSON 解析 | `_parse_llm_json()` 提取 + 修复 | 解析失败 → `_keyword_fallback()` |
| 最终兜底 | — | 关键字规则匹配 6 维度画像（completeness=0.3~0.5, confidence=0.4） |

**已知失败模式**：
- 学生输入过短（< 5 字）：关键字规则覆盖不足 → 返回默认画像
- 纯数字/乱码输入：关键字无匹配 → completeness=0.3 低质量画像

**降级信号**：`sources: ["keyword_fallback"]` → 前端可提示"画像基于粗略估计，建议完善信息"

### 2.2 PlannerAgent

| 环节 | 正常路径 | 降级路径 |
|------|---------|---------|
| LLM 调用 | `call_llm()` | 异常 → `_rule_based_plan()` |
| 最终兜底 | — | 按 course_outline 生成阶段模板 |

**降级特征**：
- 所有阶段使用统一任务模板
- `estimated_days` 基于 `knowledge_level` 的固定倍率
- 不包含个性化调整（薄弱点补习任务仅做关键词匹配）

### 2.3 ResourceAgent

| 环节 | 正常路径 | 降级路径 |
|------|---------|---------|
| LLM 调用 | `call_llm()` 流式 | 异常 → `_rule_based_resources()` |
| JSON 解析 | `_parse_and_validate()` | 非法 JSON / 缺 resources / resources 非 list → `_rule_based_resources()` |
| 字段校验 | 规范化 type/title/topic/difficulty/content | 缺少字段 → 补默认值 |
| 最终兜底 | — | 模板化骨架内容 |

**降级特征**：
- 所有资源使用骨架模板（标题、概念定义、原理、示例、要点）
- `content` 为预定义 Markdown 模板，非 LLM 生成
- 前端无感知 —— 返回结构完全相同

### 2.4 TutorAgent

| 环节 | 正常路径 | 降级路径 |
|------|---------|---------|
| 安全过滤 | `check_safety()` → safe → 继续 | `check_safety()` → blocked → 返回拦截提示 |
| LLM 调用 | `call_llm()` | 异常 → `_rule_based_tutor()` |
| RAG 检索 | `retriever.retrieve()` → 命中 | 检索失败/无命中 → 空上下文 + 降级提示 |
| JSON 解析 | `json.loads()` | 异常 → `_rule_based_tutor()` |
| 最终兜底 | — | 按风格选择预定义回答模板 |

**RAG 降级信号**：
- `references: []` 或 `references: ["建议参考课程指定教材相关章节"]` → 前端可隐藏"参考资料"区块
- `answer` 包含 "资料库中暂未查到" → 建议学生查阅教材

### 2.5 EvaluateAgent

| 环节 | 正常路径 | 降级路径 |
|------|---------|---------|
| LLM 调用 | `call_llm()` | 异常 → `_rule_based_evaluate()` |
| 统计计算 | 从 records 提取 avg_score / progress / efficiency | 空 records → 默认值 (avg_score=50, progress=0, efficiency=0) |
| 遗忘曲线 | `_compute_review_plan()` | 无历史 → 仅薄弱点出现在 review_plan 中 |
| 最终兜底 | — | 纯统计规则评估 |

**降级特征**：
- dimensions 基于硬编码阈值（≥75 掌握良好，≥50 需复习，<50 基础薄弱）
- suggestions 基于阈值分支而非 LLM 语义分析
- 没有 LLM 时 review_plan 仍可正常工作（遗忘曲线是纯数学计算）

---

## 3. RAG 降级

| 场景 | 行为 |
|------|------|
| 知识库为空 | `Retriever.retrieve()` 返回 `[]`，log WARNING "知识库为空，检索返回空结果" |
| 相似度低于阈值 | `min_similarity` 过滤，默认 0.3 |
| embedding 失败 | 异常捕获 → `rag_results = []` → 上下文为空 |
| vector_store 连接失败 | 异常捕获 → 返回空结果 |

**RAG 无依据提示**（统一）：`"资料库中未找到可靠依据"` 或 `"资料库中暂未查到相关内容，建议核实后重新提问"`

---

## 4. LLM 调用降级

```
BaseAgent.call_llm():
  Attempt 1 → 失败 → 等 1s
  Attempt 2 → 失败 → 等 2s  
  Attempt 3 → 失败 → 返回错误提示文本
```

- 重试策略：指数退避（1s → 2s）
- 最多 3 次尝试
- 3 次均失败 → 提示"内容生成失败（已重试3次），请稍后重新尝试"
- 各 Agent 根据此错误文本触发各自 `_rule_based_*()` 兜底

---

## 5. 安全模块降级

| 场景 | 行为 |
|------|------|
| content_filter 检查通过 | 正常流程 |
| 敏感内容命中 | 返回 `{safe: False, reason: "...", category: "..."}` |
| 注入攻击命中 | 返回 `{safe: False, reason: "检测到潜在注入攻击..."}` |
| 白名单匹配 | 直接放行，跳过敏感/注入检查 |

**安全拦截返回格式**（TutorAgent 示例）：
```json
{
  "answer": "⚠️ 输入包含不适当内容（violence），已被安全策略拦截。",
  "explanation_style": "auto",
  "references": [],
  "diagrams": [],
  "blocked": true,
  "block_reason": "violence"
}
```

---

## 6. 常见失败与应对

| 失败场景 | 影响范围 | 降级行为 | 用户感知 |
|---------|---------|---------|---------|
| LLM API Key 无效 | 全部 Agent | 全部走规则化 | 功能可用但建议缺乏个性化 |
| LLM 超时 | 单次调用 | 重试 3 次 → 规则化 | 等待 3-4s 后返回模板内容 |
| LLM 返回非 JSON | ResourceAgent/PlannerAgent | 回退规则化 | 无感知 |
| RAG 知识库为空 | TutorAgent | 无参考资料仍可回答 | 无参考引用 |
| embedding API 失败 | RAG 检索 | 返回空结果 | 无参考引用 |
| 输入含敏感内容 | 单次请求 | 拒绝 + 提示 | 看到安全提示 |
| 输入含注入攻击 | 单次请求 | 拒绝 | 看到安全提示 |

---

## 7. 创新点降级说明

### 遗忘曲线（Ebbinghaus）
- **正常**：基于 `R = e^(-t/S)` 计算记忆保留率，低于 60% 触发复习
- **降级**：records 为空时，仅薄弱点进入 review_plan（urgency=medium）
- **非 LLM 依赖**：遗忘曲线是纯数学计算，`_compute_review_plan()` 始终可用

### 多解释路径（TutorAgent）
- **正常**：LLM 生成 analogy/formula/visual/story 四种风格
- **降级**：每种风格有预定义模板，_rule_based_tutor() 可生成所有 4 种风格
- **Mermaid 图表**：visual 风格的 diagrams 在降级模式下仍可生成（使用固定模板）
