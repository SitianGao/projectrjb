/**
 * 共享阶段工具函数
 * 供 StageLineChart、StageResourcePage、LearningJourneyPage 等组件使用
 */

/**
 * 根据 stage.topics 匹配资源
 * 双向模糊匹配：resource.topic 包含 stage topic 或 stage topic 包含 resource.topic
 */
export function matchResourcesToStage(stage, allResources) {
  if (!stage?.topics?.length || !allResources?.length) return []
  return allResources.filter((res) => {
    const resTopic = (res.topic || '').toLowerCase()
    if (!resTopic) return false
    return stage.topics.some((t) => {
      const topic = t.toLowerCase()
      return resTopic.includes(topic) || topic.includes(resTopic)
    })
  })
}

/**
 * 计算 stage 的预计天数（汇总 tasks 的 estimated_hours / 2）
 */
export function computeStageDays(stage) {
  if (stage.estimated_days != null) return stage.estimated_days
  const hours = (stage.tasks || []).reduce(
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
  const tasks = stage.tasks || []
  if (tasks.length === 0) return 1
  const total = tasks.reduce((sum, t) => sum + (DIFFICULTY_MAP[t.difficulty] || 1), 0)
  return Math.round((total / tasks.length) * 10) / 10
}

/** 难度数值 → 文本映射 */
export const DIFFICULTY_LABELS = { 1: '初级', 2: '中级', 3: '高级', 4: '专家' }

/** 阶段状态颜色配置 */
export const STAGE_STATUS_COLORS = {
  completed: { fill: '#52c41a', border: '#389e0d', glow: 'rgba(82,196,26,0.3)' },
  in_progress: { fill: '#1677ff', border: '#0958d9', glow: 'rgba(22,119,255,0.4)' },
  locked: { fill: '#d9d9d9', border: '#bfbfbf', glow: 'rgba(217,217,217,0.2)' },
}
