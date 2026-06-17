import client from './client'

/**
 * 智能辅导相关 API
 *
 * 后端端点 (v2 统一合同):
 *   POST /api/tutor/chat             流式辅导对话（SSE）
 *   GET  /api/tutor/sessions         获取会话列表 ?student_id=
 *   POST /api/tutor/sessions         创建新会话
 *   POST /api/tutor/check            提交答案供检查
 */

// 发送辅导消息（非流式，保留兼容）
export async function askTutor(data) {
  return client.post('/tutor/chat', data)
}

// 流式辅导对话（SSE）
export async function askTutorStream(data) {
  const response = await fetch('/api/tutor/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response
}

// 获取对话历史
export async function getTutorHistory(sessionId) {
  return client.get(`/tutor/history/${sessionId}`)
}

// 获取会话列表
export async function getTutorSessions(studentId) {
  return client.get('/tutor/sessions', { params: { student_id: studentId } })
}

// 创建新会话
export async function createTutorSession(data) {
  return client.post('/tutor/sessions', data)
}

// 提交答案供检查
export async function submitAnswer(data) {
  return client.post('/tutor/check', data)
}
