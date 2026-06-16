import client from './client'

/**
 * 智能辅导相关 API
 */

// 发送辅导消息
export async function askTutor(data) {
  return client.post('/tutor/ask', data)
}

// 流式辅导对话
export async function askTutorStream(data) {
  const response = await fetch('/api/tutor/ask/stream', {
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
