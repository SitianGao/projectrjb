/**
 * 共享阶段工具函数
 * 供 StageLineChart、StageResourcePage、LearningJourneyPage 等组件使用
 */

/**
 * 根据 stage.topics 匹配资源
 * 双向模糊匹配：resource.topic 包含 stage topic 或 stage topic 包含 resource.topic
 */
export function matchResourcesToStage(stage, allResources) {
  const topics = normalizeStringList(stage?.topics)
  if (!allResources?.length) return []
  const exactStageResources = allResources.filter(
    (resource) =>
      resource.stage_id != null &&
      String(resource.stage_id) === String(stage?.stage_id),
  )
  if (exactStageResources.length > 0) return exactStageResources
  if (!topics.length) return []
  return allResources.filter((res) => {
    // 新资源必须使用 stage_id 精确关联；仅对没有 stage_id 的历史资源做 topic 兼容。
    if (res.stage_id != null) return false
    const resTopic = (res.topic || '').toLowerCase()
    if (!resTopic) return false
    return topics.some((t) => {
      const topic = t.toLowerCase()
      return resTopic.includes(topic) || topic.includes(resTopic)
    })
  })
}

/** 将历史字符串字段和新版数组字段统一为非空字符串数组。 */
export function normalizeStringList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean)
  }
  if (value == null) return []
  const text = String(value).trim()
  return text ? [text] : []
}

/** 防止历史脏数据对 tasks.map/filter/reduce 造成运行时崩溃。 */
export function normalizeTasks(value) {
  return Array.isArray(value) ? value : []
}

/**
 * 计算 stage 的预计天数（汇总 tasks 的 estimated_hours / 2）
 */
export function computeStageDays(stage) {
  if (stage.estimated_days != null) return stage.estimated_days
  const hours = normalizeTasks(stage.tasks).reduce(
    (sum, t) => sum + (t.estimated_hours || 0.5),
    0,
  )
  return Math.max(1, Math.round(hours / 2))
}

/**
 * 根据 stage_id 和 current_stage 计算状态
 * @returns {'completed' | 'in_progress' | 'locked'}
 */
export function getStageStatus(stage, currentStage) {
  const cur = Number(currentStage) || 1
  const id = Number(stage.stage_id) || 0
  if (id < cur) return 'completed'
  if (id === cur) return 'in_progress'
  return 'locked'
}

/**
 * 计算阶段难度数值（用于图表 Y 轴）
 * 取该阶段所有任务难度的平均值映射
 */
export function computeStageDifficulty(stage) {
  const DIFFICULTY_MAP = { '初级': 1, '中级': 2, '高级': 3, '专家': 4 }
  const tasks = normalizeTasks(stage.tasks)
  if (tasks.length === 0) return 1
  const total = tasks.reduce((sum, t) => sum + (DIFFICULTY_MAP[t.difficulty] || 1), 0)
  return Math.round((total / tasks.length) * 10) / 10
}

/** 难度数值 → 文本映射 */
export const DIFFICULTY_LABELS = { 1: '初级', 2: '中级', 3: '高级', 4: '专家' }

/** 队员 A 的阶段状态颜色配置（支持深色模式）。 */
export function getStageStatusColors(isDark = false) {
  if (isDark) {
    return {
      completed: { fill: '#73d13d', border: '#52c41a', glow: 'rgba(115,209,61,0.3)' },
      in_progress: { fill: '#4dabff', border: '#2989e8', glow: 'rgba(77,171,255,0.4)' },
      locked: { fill: '#555', border: '#444', glow: 'rgba(85,85,85,0.2)' },
    }
  }
  return {
    completed: { fill: '#52c41a', border: '#389e0d', glow: 'rgba(82,196,26,0.3)' },
    in_progress: { fill: '#1677ff', border: '#0958d9', glow: 'rgba(22,119,255,0.4)' },
    locked: { fill: '#d9d9d9', border: '#bfbfbf', glow: 'rgba(217,217,217,0.2)' },
  }
}

export const STAGE_STATUS_COLORS = getStageStatusColors()
