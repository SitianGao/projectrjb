export function createLocalAgentJob(id = `job-${Date.now()}`) {
  return {
    id,
    status: 'created',
    steps: [
      { key: 'profile', title: 'AI 画像助手 — 确认画像', status: 'waiting' },
      { key: 'planner', title: 'AI 学习规划助手 — 生成学习路径', status: 'waiting' },
      { key: 'resource', title: 'AI 资源助手 — 生成资源蓝图', status: 'waiting' },
      { key: 'done', title: '生成结果确认', status: 'waiting' },
    ],
  }
}

export function reduceAgentJob(job, event) {
  const activeStep = event?.step || (event?.type === 'data' ? 'planner' : event?.type)
  const done = event?.type === 'done'
  const failed = event?.type === 'error'
  return {
    ...job,
    status: failed ? 'failed' : done ? 'done' : 'running',
    message: event?.message || job.message,
    error: failed ? event?.message : null,
    steps: job.steps.map((step) => {
      if (done) return { ...step, status: 'done' }
      if (failed && step.key === activeStep) return { ...step, status: 'failed' }
      if (step.key === activeStep) return { ...step, status: 'running', message: event?.message }
      const order = job.steps.findIndex((item) => item.key === step.key)
      const activeOrder = job.steps.findIndex((item) => item.key === activeStep)
      if (activeOrder > order) return { ...step, status: 'done' }
      return step
    }),
  }
}
