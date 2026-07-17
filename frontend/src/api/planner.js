import client from './client'

/**
 * 学习规划相关 API
 *
 * 后端 API 端点：
 *   POST /api/planner/generate    生成学习路径（SSE 流式），请求体 {student_id, goal?}
 *   GET  /api/planner/{student_id} 获取学生当前学习路径（JSON）
 *
 * SSE 事件类型（generate 接口）：
 *   start  — 流开始，含元信息
 *   delta  — 增量文本片段（LLM 思考过程）
 *   data   — 结构化阶段数据（PathTimeline 的 stages）
 *   error  — 错误信息
 *   done   — 流结束
 *
 * PathTimeline 数据形状（stages 数组）：
 *   [{
 *     "stage_id": 1,
 *     "title": "...",
 *     "description": "...",
 *     "objectives": ["..."],
 *     "topics": ["..."],
 *     "tasks": [{
 *       "task_id": "1-1",
 *       "type": "study",
 *       "description": "...",
 *       "estimated_days": 4,
 *       "difficulty": "初级",
 *       "prerequisites": [...]
 *     }]
 *   }]
 */

/**
 * 生成学习路径（SSE 流式）
 *
 * 用法示例：
 *   const response = await generateLearningPath({ student_id: 'xxx', goal: '...' })
 *   const reader = response.body.getReader()
 *   // 逐行读取 SSE 事件: start / delta / data / error / done
 *
 * @param {{ student_id: string, goal?: string }} params
 * @returns {Promise<Response>} fetch Response，通过 body reader 读取 SSE 流
 */
export async function generateLearningPath({ student_id, goal } = {}) {
  const response = await fetch('/api/planner/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id, goal }),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response
}

/**
 * 获取学生当前学习路径
 *
 * @param {string} studentId — 学生 ID
 * @returns {Promise<{
 *   student_id: string,
 *   title?: string,
 *   stages: Array<{
 *     stage_id: number,
 *     title: string,
 *     description: string,
 *     objectives: string[],
 *     topics: string[],
 *     tasks: Array<{
 *       task_id: string,
 *       type: string,
 *       description: string,
 *       estimated_days: number,
 *       difficulty: string,
 *       prerequisites: string[]
 *     }>
 *   }>,
 *   created_at?: string,
 *   updated_at?: string
 * }>}
 */
export async function getLearningPath(studentId) {
  return client.get(`/planner/${studentId}`)
}

// 队员 A 的“我的课程/路径历史”页面需要读取全部路径版本。
export async function getAllLearningPaths(studentId) {
  return client.get(`/planner/${studentId}/all`)
}

export async function getLearningPathById(studentId, pathId) {
  return client.get(`/planner/${studentId}/path/${pathId}`)
}

// 后端实现为安全归档，不直接物理删除关联资源与学习记录。
export async function deleteLearningPath(studentId, pathId) {
  return client.delete(`/planner/${studentId}/${pathId}`)
}
