import client from './client'

/**
 * 学习评估相关 API
 */

// 获取学生评估报告
export async function getEvaluation(studentId) {
  return client.get(`/evaluate/${studentId}`)
}

// 生成评估报告
export async function generateEvaluation(data) {
  return client.post('/evaluate/generate', data)
}

// 流式生成评估
export async function generateEvaluationStream(data) {
  const response = await fetch('/api/evaluate/generate/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response
}

// 获取评估历史
export async function getEvaluationHistory(studentId) {
  return client.get(`/evaluate/${studentId}/history`)
}

// 获取学习进度统计
export async function getProgressStats(studentId) {
  return client.get(`/evaluate/${studentId}/progress`)
}

// 提交自评
export async function submitSelfEval(data) {
  return client.post('/evaluate/self', data)
}
