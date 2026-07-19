import { normalizeStringList, normalizeTasks } from './stageUtils'

const STATUS_ALIASES = {
  done: 'completed',
  finished: 'completed',
  complete: 'completed',
  completed: 'completed',
  current: 'active',
  active: 'active',
  in_progress: 'active',
  pending: 'pending',
  todo: 'pending',
  not_started: 'pending',
  locked: 'locked',
  已完成: 'completed',
  完成: 'completed',
  进行中: 'active',
  当前学习: 'active',
  未开始: 'pending',
  待开始: 'pending',
  锁定: 'locked',
  未解锁: 'locked',
}

function clampNumber(value, min, max) {
  const num = Number(value)
  if (!Number.isFinite(num)) return min
  return Math.max(min, Math.min(max, num))
}

export function clampPercent(value) {
  return Math.round(clampNumber(value, 0, 100))
}

export function safeTaskProgress(completed, total) {
  const safeTotal = Math.max(0, Number(total) || 0)
  const safeCompleted = safeTotal === 0 ? 0 : clampNumber(completed, 0, safeTotal)
  return {
    completed: safeCompleted,
    total: safeTotal,
    percent: safeTotal > 0 ? clampPercent((safeCompleted / safeTotal) * 100) : 0,
  }
}

function normalizeStatus(status) {
  return STATUS_ALIASES[String(status || '').trim().toLowerCase()] || 'pending'
}

function toMinutes(task, fallback = 20) {
  const hours = Number(task?.estimated_hours)
  if (Number.isFinite(hours) && hours > 0) return Math.max(5, Math.round(hours * 60))
  const minutes = Number(task?.estimatedMinutes ?? task?.estimated_minutes)
  if (Number.isFinite(minutes) && minutes > 0) return Math.round(minutes)
  return fallback
}

function uniqueRawTasks(stage) {
  const seen = new Set()
  return normalizeTasks(stage?.tasks).filter((task, index) => {
    if (!task || typeof task !== 'object') return false
    const key = String(task.task_id || task.id || task.description || task.task || index).trim()
    if (!key || seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function pickTasks(rawTasks, matcher) {
  return rawTasks.filter((task, index) => matcher(String(task.type || task.resource_type || '').toLowerCase(), task, index))
}

function joinTaskText(tasks) {
  return tasks
    .map((task) => String(task.description || task.task || task.title || '').trim())
    .filter(Boolean)
}

function slotStatus(tasks, fallback = 'pending') {
  const statuses = tasks.map((task) => normalizeStatus(task.status))
  if (statuses.includes('active')) return 'active'
  if (statuses.length && statuses.every((status) => status === 'completed')) return 'completed'
  if (statuses.includes('completed')) return 'completed'
  return fallback
}

function sanitizeSequence(tasks) {
  const unique = []
  const seen = new Set()
  tasks.forEach((task) => {
    if (seen.has(task.id)) return
    seen.add(task.id)
    unique.push({ ...task, status: normalizeStatus(task.status) })
  })

  let activeIndex = unique.findIndex((task) => task.status === 'active')
  if (activeIndex < 0) {
    activeIndex = unique.findIndex((task) => task.status !== 'completed' && task.status !== 'locked')
    if (activeIndex >= 0) unique[activeIndex] = { ...unique[activeIndex], status: 'active' }
  }

  return unique.map((task, index) => {
    if (task.type === 'exam') {
      const previousDone = unique.slice(0, index).every((item) => item.status === 'completed')
      if (!previousDone && task.status !== 'completed' && index !== activeIndex) {
        return { ...task, status: 'locked' }
      }
    }
    if (activeIndex >= 0 && index > activeIndex && task.status === 'active') {
      return { ...task, status: 'pending' }
    }
    return task
  })
}

export function buildStageLearningTasks(stage) {
  if (!stage) return []

  const stageId = String(stage.stage_id || 1)
  const objectives = normalizeStringList(stage.objectives)
  const topics = normalizeStringList(stage.topics)
  const rawTasks = uniqueRawTasks(stage)

  // ── v3: Use real agent-generated tasks instead of a fixed template ──
  if (rawTasks.length > 0) {
    const sequence = rawTasks
      // Filter out goal/objective tasks — objectives belong in stage intro
      .filter((task) => {
        const type = String(task.type || task.task_type || task.resource_type || '').toLowerCase()
        return type !== 'goal' && type !== 'objective'
      })
      .map((task, index) => {
        const type = String(task.type || task.task_type || task.resource_type || '').toLowerCase()
        const title = task.title || task.task || task.description || `任务 ${index + 1}`
        const description = task.description || task.task || ''
        const estimatedMinutes = toMinutes(task)
        const status = normalizeStatus(task.status)
        const isDynamic = Boolean(task.dynamic_source)
        const unlockCondition = task.unlock_condition || null

        // Map backend task_type to frontend display type
        let frontendType = 'document'
        if (/exercise|quiz|practice|check/.test(type)) frontendType = 'quiz'
        else if (/mindmap|diagram|graph|map/.test(type)) frontendType = 'diagram'
        else if (/interactive_classroom|classroom|openmaic/.test(type)) frontendType = 'interactive_classroom'
        else if (/test|exam|assessment/.test(type)) frontendType = 'exam'
        else if (/code/.test(type)) frontendType = 'code'
        else if (/weakness_fix/.test(type)) frontendType = 'quiz'
        else if (/document|reading|lecture/.test(type)) frontendType = 'document'

        // Build content from task data
        const contentParts = []
        if (description) contentParts.push(`### ${title}\n\n${description}`)
        if (isDynamic) {
          const sourceLabel = String(task.dynamic_source || '').replace('evaluation_weakness:', '评估薄弱点: ').replace('profile_gap:', '知识缺口: ').replace('interest:', '兴趣方向: ')
          contentParts.push(`\n> 🤖 **AI 根据近期学习诊断新增**\n> 来源：${sourceLabel}`)
        }
        const content = contentParts.join('\n') || `### ${title}`

        return {
          id: task.task_id || task.id || `${stageId}-task-${index}`,
          type: frontendType,
          title,
          objective: description || title,
          content,
          estimatedMinutes,
          status,
          dynamicSource: task.dynamic_source || null,
          unlockCondition,
          difficulty: task.difficulty || null,
        }
      })

    return sanitizeSequence(sequence)
  }

  // ── Fallback: no agent-generated tasks → minimal defaults ──
  return sanitizeSequence([
    {
      id: `${stageId}-document`,
      type: 'document',
      title: '核心讲义',
      objective: `掌握${stage.title || '当前阶段'}的核心概念`,
      content: [
        `### 核心知识内容`,
        stage.description || `围绕「${stage.title || '当前阶段'}」完成概念阅读和笔记整理。`,
        topics.length ? `\n### 关键知识点\n${topics.map((item) => `- ${item}`).join('\n')}` : '',
      ].filter(Boolean).join('\n'),
      estimatedMinutes: 25,
      status: 'active',
    },
    {
      id: `${stageId}-exercise`,
      type: 'quiz',
      title: '知识检查',
      objective: '确认概念是否真正掌握',
      content: '- 用自己的话解释本阶段 2 个核心概念。\n- 完成基础练习，标记不确定的问题。',
      estimatedMinutes: 20,
      status: 'pending',
    },
    {
      id: `${stageId}-assessment`,
      type: 'exam',
      title: '阶段测评',
      objective: '完成阶段测评',
      content: '- 回顾本阶段笔记。\n- 完成阶段测评。\n- 根据错题结果决定是否回看。',
      estimatedMinutes: 30,
      status: 'locked',
    },
  ])
}

export function getCurrentStage(path) {
  const stages = Array.isArray(path?.stages) ? path.stages : []
  if (!stages.length) return null
  const currentStage = path?.current_stage ?? 1
  return (
    stages.find((stage) => String(stage.stage_id) === String(currentStage))
    || stages.find((stage) => Number(stage.stage_id) === Number(currentStage))
    || stages[0]
  )
}

export function findCurrentLearningTask(tasks = []) {
  return (
    tasks.find((task) => task.status === 'active')
    || tasks.find((task) => task.status === 'pending')
    || tasks.find((task) => task.status !== 'locked')
    || null
  )
}

export function getCurrentLearningTarget(path) {
  const stage = getCurrentStage(path)
  const tasks = buildStageLearningTasks(stage)
  return {
    stage,
    tasks,
    task: findCurrentLearningTask(tasks),
  }
}

export function getTasksProgress(tasks = []) {
  const ids = new Set()
  let completed = 0
  tasks.forEach((task) => {
    if (!task?.id || ids.has(task.id)) return
    ids.add(task.id)
    if (task.status === 'completed') completed += 1
  })
  return safeTaskProgress(completed, ids.size)
}

export function getPathProgress(path, externalCompleted) {
  const stages = Array.isArray(path?.stages) ? path.stages : []
  const allTasks = stages.flatMap((stage) => buildStageLearningTasks(stage))
  const local = getTasksProgress(allTasks)
  if (externalCompleted == null) return local
  return safeTaskProgress(externalCompleted, local.total)
}
