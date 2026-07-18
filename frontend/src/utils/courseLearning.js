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
  const lectureTasks = pickTasks(rawTasks, (type, task, index) =>
    /document|reading|study|lecture|text|resource/.test(type)
    || (!/exercise|quiz|test|exam|code|mindmap|diagram|interactive_classroom|classroom|openmaic/.test(type) && index < Math.max(1, rawTasks.length - 1)),
  )
  const diagramTasks = pickTasks(rawTasks, (type) => /mindmap|diagram|graph|map/.test(type))
  const classroomTasks = pickTasks(rawTasks, (type) => /interactive_classroom|classroom|openmaic/.test(type))
  const quizTasks = pickTasks(rawTasks, (type) => /exercise|quiz|practice|check/.test(type))
  const examTasks = pickTasks(rawTasks, (type) => /test|exam|assessment/.test(type))

  const lectureLines = joinTaskText(lectureTasks)
  const diagramLines = joinTaskText(diagramTasks)
  const classroomLines = joinTaskText(classroomTasks)
  const quizLines = joinTaskText(quizTasks)
  const examLines = joinTaskText(examTasks)

  const sequence = [
    {
      id: `${stageId}-goal`,
      type: 'objective',
      title: '学习目标',
      objective: objectives[0] || stage.description || `理解${stage.title || '当前阶段'}的学习目标`,
      content: [
        `### 本阶段目标`,
        ...(objectives.length ? objectives.map((item) => `- ${item}`) : [`- ${stage.description || `建立对「${stage.title || '当前知识点'}」的整体认识。`}`]),
        topics.length ? `\n### 关键知识点\n${topics.map((item) => `- ${item}`).join('\n')}` : '',
      ].filter(Boolean).join('\n'),
      estimatedMinutes: 10,
      status: slotStatus([], 'active'),
    },
    {
      id: `${stageId}-lecture`,
      type: 'lecture',
      title: '核心讲义',
      objective: `掌握${stage.title || '当前阶段'}的核心概念和基本方法`,
      content: [
        `### 核心知识内容`,
        stage.description || `围绕「${stage.title || '当前阶段'}」完成概念阅读、例题理解和笔记整理。`,
        lectureLines.length ? `\n### 学习任务\n${lectureLines.map((item) => `- ${item}`).join('\n')}` : '',
      ].filter(Boolean).join('\n'),
      estimatedMinutes: lectureTasks.reduce((sum, task) => sum + toMinutes(task, 25), 0) || 25,
      status: slotStatus(lectureTasks),
    },
    {
      id: `${stageId}-diagram`,
      type: 'diagram',
      title: '概念图解',
      objective: '把知识点之间的关系整理成可视化结构',
      content: [
        `### 概念关系`,
        topics.length ? topics.map((item, index) => `${index + 1}. ${item}`).join('\n') : '将本阶段概念按“定义 - 性质 - 应用 - 易错点”整理成结构图。',
        diagramLines.length ? `\n### 图解任务\n${diagramLines.map((item) => `- ${item}`).join('\n')}` : '',
      ].filter(Boolean).join('\n'),
      estimatedMinutes: diagramTasks.reduce((sum, task) => sum + toMinutes(task, 15), 0) || 15,
      status: slotStatus(diagramTasks),
    },
  ]

  if (classroomTasks.length) {
    const firstClassroomTask = classroomTasks[0]
    sequence.push({
      id: String(firstClassroomTask.task_id || firstClassroomTask.id || `${stageId}-interactive-classroom`),
      type: 'interactive_classroom',
      title: firstClassroomTask.title || 'OpenMAIC 在线课堂',
      objective: firstClassroomTask.description || `通过互动课堂掌握${stage.title || '当前阶段'}的关键过程`,
      content: [
        `### 互动课堂任务`,
        classroomLines.length
          ? classroomLines.map((item) => `- ${item}`).join('\n')
          : '- 进入 OpenMAIC 在线课堂完成讲授、模拟实验、AI 提问和知识检查。',
      ].join('\n'),
      estimatedMinutes: classroomTasks.reduce((sum, task) => sum + toMinutes(task, 25), 0) || 25,
      status: slotStatus(classroomTasks),
    })
  }

  sequence.push(
    {
      id: `${stageId}-check`,
      type: 'quiz',
      title: '知识检查',
      objective: '通过小测确认概念是否真正掌握',
      content: [
        `### 自检任务`,
        quizLines.length ? quizLines.map((item) => `- ${item}`).join('\n') : '- 用自己的话解释本阶段 2 个核心概念。\n- 完成 3 道基础练习，并标记不确定的问题。',
      ].join('\n'),
      estimatedMinutes: quizTasks.reduce((sum, task) => sum + toMinutes(task, 20), 0) || 20,
      status: slotStatus(quizTasks),
    },
    {
      id: `${stageId}-assessment`,
      type: 'exam',
      title: '阶段测评',
      objective: '完成阶段测评并决定是否进入下一阶段',
      content: [
        `### 阶段测评`,
        examLines.length ? examLines.map((item) => `- ${item}`).join('\n') : '- 回顾本阶段笔记。\n- 完成阶段测评。\n- 根据错题结果决定是否回看核心讲义。',
      ].join('\n'),
      estimatedMinutes: examTasks.reduce((sum, task) => sum + toMinutes(task, 30), 0) || 30,
      status: slotStatus(examTasks, 'locked'),
    },
  )

  return sanitizeSequence(sequence)
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
