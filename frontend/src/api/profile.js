import client from './client'

/**
 * 画像相关 API
 */

// 获取学生画像
export async function getProfile(studentId) {
  return client.get(`/profile/${studentId}`)
}

// 创建/更新学生画像
export async function upsertProfile(data) {
  return client.post('/profile', data)
}

// 通过对话方式补充画像信息（非流式）
export async function chatWithProfile(studentId, message) {
  return client.post(`/profile/${studentId}/chat`, { message })
}

// 流式画像对话（useChat hook 消费）
// 返回 fetch Response，调用方通过 response.body.getReader() 读取 SSE 流
export async function chatWithProfileStream(studentId, message, signal) {
  const response = await fetch(`/api/profile/${studentId}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal,  // 支持 AbortController 取消
  })
  if (!response.ok) {
    const errText = await response.text().catch(() => '')
    throw new Error(errText || `HTTP ${response.status}`)
  }
  return response
}

// 获取画像历史
export async function getProfileHistory(studentId) {
  return client.get(`/profile/${studentId}/history`)
}

// 获取测试用例画像（3个典型案例）
export async function getTestCases() {
  return client.get('/profile/test/cases')
}
