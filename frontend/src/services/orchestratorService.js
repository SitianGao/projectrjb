import { getCourseLearningPath } from '../api/courseLearning'
import { invalidateHomeDashboard } from '../utils/dashboardEvents'
import { streamSse } from '../utils/sseClient'

export async function initializeCourseLearning({ courseId, goal, onEvent }) {
  const token = localStorage.getItem('auth_token')

  let pathData = null

  await streamSse(
    () => fetch(
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
    ),
    {
      onStart: (event) => onEvent?.(event),
      onProgress: (event) => onEvent?.(event),
      onData: (event) => {
        onEvent?.(event)
        const data = event.data || event
        if (data?.stages?.length) {
          pathData = data
        }
      },
      onError: (err) => {
        throw err
      },
      onDone: () => onEvent?.({ type: 'done' }),
    },
  )

  const scoped = await getCourseLearningPath(courseId).catch(() => null)
  const result = scoped?.path || pathData
  if (!result?.stages?.length) throw new Error('未生成有效学习路径')
  invalidateHomeDashboard(courseId, 'path_adjusted')
  return result
}
