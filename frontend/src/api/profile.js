import client from './client'

/**
 * 画像相关 API
 *
 * 后端 API 端点：
 *   POST /api/profile/chat        对话式画像构建（SSE 流式）
 *   GET  /api/profile/{student_id} 获取学生画像
 *   PUT  /api/profile/{student_id} 更新画像
 *
 * SSE 事件类型（chat 接口）：
 *   chat          — LLM 自然语言回复增量
 *   profile_update — 画像更新 JSON
 *   error         — 错误信息
 *   done          — 流结束
 */

/**
 * 获取学生画像
 * @param {string} studentId — 学生 ID
 * @returns {Promise<object>} 直接返回画像数据对象（已解包 success/data）
 */
export async function getProfile(studentId) {
  const res = await client.get(`/profile/${studentId}`)
  return res?.data ?? res
}

/**
 * 更新学生画像（增量）
 * @param {string} studentId — 学生 ID
 * @param {object} data — 要更新的字段
 * @param {string} [data.knowledge_level]
 * @param {string} [data.learning_goal]
 * @param {string} [data.cognitive_style]
 * @param {string[]} [data.weakness]
 * @param {string[]} [data.interest]
 * @param {string} [data.pace_preference]
 * @returns {Promise<object>} 直接返回画像数据对象（已解包 success/data）
 */
export async function updateProfile(studentId, data) {
  const res = await client.put(`/profile/${studentId}`, data)
  return res?.data ?? res
}

/**
 * 对话式画像构建（SSE 流式）
 *
 * 用法：
 *   const response = await startProfileChat({ student_id, message })
 *   const reader = response.body.getReader()
 *   // 逐行读取 SSE 事件: chat / profile_update / error / done
 *
 * @param {object} params
 * @param {string} params.student_id      — 学生 ID
 * @param {string} params.message         — 当前轮用户消息
 * @param {string[]} [params.history]     — 历史对话消息
 * @param {object} [params.current_profile] — 已有画像（增量更新时传入）
 * @returns {Promise<Response>} fetch Response，通过 body reader 读取 SSE 流
 */
export async function startProfileChat({ student_id, message, history, current_profile } = {}) {
  const response = await fetch('/api/profile/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id,
      message,
      ...(history && { history }),
      ...(current_profile && { current_profile }),
    }),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response
}
