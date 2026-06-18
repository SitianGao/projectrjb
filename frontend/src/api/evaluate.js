import client from './client'

/**
 * 学习评估相关 API
 *
 * 后端端点 (v2 统一合同):
 *   POST /api/evaluate/start             发起评估任务，返回 { task_id }
 *   GET  /api/evaluate/report/{student_id} 获取学生评估报告
 *   GET  /api/evaluate/record?student_id= 获取评估历史
 *   GET  /api/task/{task_id}/status       查询异步任务进度
 */

// 发起评估任务 → 返回 { task_id }
export async function generateEvaluation(data) {
  return client.post('/evaluate/start', data)
}

// 获取学生评估报告
export async function getEvaluation(studentId) {
  return client.get(`/evaluate/report/${studentId}`)
}

// 获取评估历史 / 记录
export async function getEvaluationHistory(studentId) {
  return client.get('/evaluate/record', { params: { student_id: studentId } })
}

// 获取学习进度统计（保留兼容，后端可能合并入 report 接口）
export async function getProgressStats(studentId) {
  return client.get(`/evaluate/report/${studentId}/progress`)
}

// 流式生成评估（保留兼容，优先使用 generateEvaluation + 轮询）
export async function generateEvaluationStream(data) {
  const response = await fetch('/api/evaluate/start/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response
}

// 提交自评
export async function submitSelfEval(data) {
  return client.post('/evaluate/self', data)
}
