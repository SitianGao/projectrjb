import { getCourseLearningPath } from '../api/courseLearning'

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

export async function initializeCourseLearning({ courseId, goal, onEvent }) {
  const token = localStorage.getItem('auth_token')
  const response = await fetch(
    `/api/courses/${encodeURIComponent(courseId)}/initialize/stream`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        goal,
        message: goal ? `我已确认课程画像，学习目标是：${goal}` : '我已确认当前课程画像',
      }),
    },
  )
  if (!response.ok) throw new Error(`课程初始化失败 (${response.status})`)
  if (!response?.body) throw new Error('当前浏览器不支持流式生成')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let pathData = null

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
      }
      if (event.type === 'error') throw new Error(event.message || '学习路径生成失败')
    }
  }

  const scoped = await getCourseLearningPath(courseId).catch(() => null)
  const result = scoped?.path || pathData
  if (!result?.stages?.length) throw new Error('未生成有效学习路径')
  return result
}
