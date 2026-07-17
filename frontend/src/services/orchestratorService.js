import { generateLearningPath, getLearningPath } from '../api/planner'

function parseSSEPayload(line) {
  if (!line.startsWith('data: ')) return null
  const raw = line.slice(6).trim()
  if (!raw || raw === '[DONE]') return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export async function initializeCourseLearning({ studentId, goal, onEvent }) {
  onEvent?.({ type: 'start', step: 'profile', message: '画像确认完成，准备生成学习路径' })
  const response = await generateLearningPath({ student_id: studentId, goal })
  if (!response?.body) throw new Error('当前浏览器不支持流式生成')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let pathData = null

  onEvent?.({ type: 'running', step: 'planner', message: 'PlannerAgent 正在规划阶段和任务' })
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      const event = parseSSEPayload(line)
      if (!event) continue
      onEvent?.(event)
      const data = event.data || event
      if (event.type === 'data' && data?.stages?.length) {
        pathData = data
        onEvent?.({ type: 'running', step: 'resource', message: 'ResourceAgent 已收到路径上下文，准备生成资源蓝图' })
      }
      if (event.type === 'error') throw new Error(event.message || '学习路径生成失败')
    }
  }

  const savedPath = await getLearningPath(studentId).catch(() => null)
  const result = savedPath || pathData
  if (!result?.stages?.length) throw new Error('未生成有效学习路径')
  onEvent?.({ type: 'done', step: 'done', message: '学习路径生成完成', data: result })
  return result
}
