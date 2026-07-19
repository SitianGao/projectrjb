// ── 统一评估标签映射 ──

// 评估范围（对齐后端时间维度 + 前端范围维度）
export const SCOPE_LABELS = {
  // 后端值
  last_7_days: '近 7 天评估',
  last_30_days: '近 30 天评估',
  all: '全部历史评估',
  course_all: '全课程评估',
  current_stage: '当前阶段评估',
  custom: '自定义范围评估',
  // 前端遗留值（兼容旧代码）
  full: '全课程评估',
  stage: '阶段评估',
  topic: '知识点评估',
  weak_point: '薄弱点专项',
  course: '课程评估',
  task: '任务评估',
}

// 生成来源
export const GENERATION_SOURCE_LABELS = {
  ai_enhanced: 'AI 增强',
  rule_based: '规则引擎',
  fallback: '兜底模板',
  manual: '手动触发',
}

// 触发方式
export const TRIGGER_LABELS = {
  auto: '自动评估',
  manual: '手动评估',
  scheduled: '定时评估',
  stage_complete: '阶段完成',
  task_complete: '任务完成',
  on_demand: '按需评估',
}

// 调整动作
export const ADJUSTMENT_ACTION_LABELS = {
  add_topics: '新增知识点',
  remove_topics: '移除知识点',
  reorder: '调整顺序',
  change_difficulty: '调整难度',
  skip_stage: '跳过阶段',
  revisit_stage: '回炉阶段',
  add_exercise: '增加练习',
  reduce_exercise: '减少练习',
  change_pace: '调整节奏',
  suggest_review: '建议复习',
}

// 调整状态
export const ADJUSTMENT_STATUS_LABELS = {
  pending: '待确认',
  applied: '已应用',
  dismissed: '已忽略',
  expired: '已过期',
}

// 趋势标签（对齐后端 _build_trend 返回值）
export const TREND_LABELS = {
  // 后端值
  insufficient_data: '数据不足',
  recovering: '正在恢复',
  improving: '正在改善',
  declining: '有所下滑',
  stable: '保持稳定',
  // 前端遗留值
  up: '上升趋势 ↑',
  down: '下降趋势 ↓',
  flat: '基本持平',
  mixed: '波动中',
}

// 维度标签
export const DIMENSION_LABELS = {
  knowledge: '知识点掌握',
  application: '应用能力',
  analysis: '分析能力',
  creativity: '创新能力',
  engagement: '学习投入',
  consistency: '学习持续性',
}

// 难度标签（对齐后端中英文混用）
export const DIFFICULTY_LABELS = {
  // 后端中文值
  '初级': '入门',
  '中级': '进阶',
  '中高级': '高级',
  '高级': '专家',
  // 后端英文值（练习题）
  easy: '入门',
  medium: '进阶',
  hard: '高级',
  // 前端遗留值
  beginner: '入门',
  intermediate: '进阶',
  advanced: '高级',
  expert: '专家',
}

// 资源类型标签
export const RESOURCE_TYPE_LABELS = {
  document: '讲义',
  exercise: '练习题',
  code: '代码示例',
  mindmap: '思维导图',
  review: '复习资料',
}

// ── 辅助函数 ──

/** 评估范围 → 中文 */
export function scopeLabel(scopeType) {
  if (!scopeType) return '未知范围'
  return SCOPE_LABELS[scopeType] || scopeType
}

// AI 来源值（后端可用：agent / rule_fallback / rule）
const AI_SOURCES = new Set(['ai', 'ai_enhanced', 'llm', 'agent'])

/** 报告 → 诊断类型中文 */
export function diagnosticLabel(report) {
  if (!report) return '未知来源'
  const source = report.generationSource || report.generation_source || ''
  if (AI_SOURCES.has(source)) return 'AI 学习诊断'
  if (source === 'rule_fallback') return 'AI 诊断（降级）'
  return '基础统计诊断'
}

/** 报告 → 图标文本 */
export function diagnosticIcon(report) {
  if (!report) return '📊'
  const source = report.generationSource || report.generation_source || ''
  if (AI_SOURCES.has(source)) return '🤖'
  if (source === 'rule_fallback') return '⚠️'
  return '📊'
}

/** 报告 → 是否 AI 增强 */
export function isAiEnhanced(report) {
  if (!report) return false
  const source = report.generationSource || report.generation_source || ''
  return AI_SOURCES.has(source)
}

/** 置信度 0-1 → 等级中文 */
export function confidenceText(confidence) {
  if (confidence == null) return '未知'
  if (confidence >= 0.8) return '高'
  if (confidence >= 0.5) return '中'
  return '低'
}

/** 趋势 → 中文 */
export function trendLabel(trend) {
  if (!trend) return '暂无趋势数据'
  return TREND_LABELS[trend] || trend
}

/** 数据不足原因 → 摘要 */
export function summarizeInsufficientReason(reason) {
  if (!reason) return '当前学习数据尚不足以生成完整评估报告，请先完成学习任务或课堂互动。'
  if (typeof reason === 'string') return reason
  if (reason.message) return reason.message
  return '数据不足，请继续学习以积累更多评估依据。'
}

/** 调整动作 → 中文 */
export function adjustmentActionLabel(action) {
  if (!action) return '未知操作'
  return ADJUSTMENT_ACTION_LABELS[action] || action
}

/** 调整状态 → 中文 */
export function adjustmentStatusLabel(status) {
  if (!status) return '未知状态'
  return ADJUSTMENT_STATUS_LABELS[status] || status
}
