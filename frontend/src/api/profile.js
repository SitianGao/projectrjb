import client from './client'

/**
 * 画像相关 API
 *
 * 后端端点 (v2 统一合同):
 *   POST /api/profile/chat           对话式画像构建（SSE 流式）
 *   GET  /api/profile/{student_id}   获取学生画像
 *   PUT  /api/profile/{student_id}   更新画像
 *
 * SSE 事件类型（chat 接口）：
 *   chat           — LLM 自然语言回复增量
 *   profile_update — 画像更新 JSON
 *   error          — 错误信息
 *   done           — 流结束
 */

// 获取学生画像（client.js 已自动解包 success/data，直接返回 data）
export async function getProfile(studentId) {
  return client.get(`/profile/${studentId}`)
}

// 更新学生画像
export async function updateProfile(studentId, data) {
  return client.put(`/profile/${studentId}`, data)
}

/**
 * 对话式画像构建（SSE 流式）
 *
 * @param {object} params
 * @param {string} params.student_id       — 学生 ID
 * @param {string} params.message          — 当前轮用户消息
 * @param {string[]} [params.history]      — 历史对话消息
 * @param {object} [params.current_profile] — 已有画像（增量更新时传入）
 * @returns {Promise<Response>} fetch Response，SSE 流
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
