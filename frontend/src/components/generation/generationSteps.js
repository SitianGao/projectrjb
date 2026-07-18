export const GENERATION_STEPS = [
  {
    key: 'outline',
    title: '生成课程大纲',
    subtitle: 'AI 正在分析学习目标与知识体系，构建个性化课程框架…',
    icon: '📋',
  },
  {
    key: 'plan',
    title: '生成阶段规划',
    subtitle: '正在拆解学习路径，划分学习阶段与关键任务节点…',
    icon: '🗂️',
  },
  {
    key: 'resources',
    title: '匹配学习资源',
    subtitle: '多智能体协同检索与生成：讲义、导图、PPT、练习、代码案例…',
    icon: '🔍',
  },
  {
    key: 'content',
    title: '生成课堂内容',
    subtitle: '正在编排教学幻灯片、随堂测验与互动环节…',
    icon: '⚙️',
  },
  {
    key: 'classroom',
    title: '组合 AI 互动课堂',
    subtitle: '整合全部资源，封装为沉浸式互动课堂体验…',
    icon: '🚀',
  },
]

const STEP_SIZE = 100 / GENERATION_STEPS.length

export function getCurrentStepIndex(overallPercent) {
  return Math.min(Math.floor(overallPercent / STEP_SIZE), GENERATION_STEPS.length - 1)
}

export function getStepProgress(overallPercent, stepIndex) {
  const segmentStart = stepIndex * STEP_SIZE
  if (overallPercent <= segmentStart) return 0
  if (overallPercent >= segmentStart + STEP_SIZE) return 100
  return ((overallPercent - segmentStart) / STEP_SIZE) * 100
}
