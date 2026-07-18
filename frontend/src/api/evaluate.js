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

export async function getCourseEvaluation({ student_id, course_id, scope_type = 'last_30_days', stage_id, start_at, end_at }) {
  return client.get(`/evaluate/courses/${course_id}/latest`, {
    params: { student_id, scope_type, stage_id, start_at, end_at },
  })
}

export async function getEvaluationReport(reportId) {
  return client.get(`/evaluate/reports/${reportId}`)
}

// 获取评估历史 / 记录
export async function getEvaluationHistory(studentId) {
  return client.get('/evaluate/record', { params: { student_id: studentId } })
}

export async function getReviewFeed(studentId) {
  const report = await getEvaluation(studentId)
  const items = report?.reviewPlan || report?.review_plan || []
  return { items, total: items.length }
}

export async function getWrongBook(studentId, status = 'unmastered') {
  try {
    return await client.get('/evaluate/wrong-book', { params: { student_id: studentId, status } })
  } catch {
    return { items: [], total: 0 }
  }
}

export async function updateWrongQuestion(questionId, payload) {
  try {
    return await client.patch(`/evaluate/wrong-book/${questionId}`, payload)
  } catch {
    return { id: questionId, ...payload }
  }
}

export async function getEvaluationReports({ student_id, course_id, limit = 20 }) {
  return client.get(`/evaluate/history/${student_id}`, { params: { course_id, limit } })
}

export async function recordLearning(data) {
  return client.post('/evaluate/record', data)
}

export async function adaptLearningJourney(data) {
  await client.post('/evaluate/start', data)
  const evaluation = await getEvaluation(data.student_id)
  return {
    evaluation,
    path_adjustments: evaluation?.pathAdjustments || evaluation?.path_adjustments || [],
    review_plan: evaluation?.reviewPlan || evaluation?.review_plan || [],
  }
}

export async function submitExerciseAnswer(data) {
  const score = data.is_correct ? 100 : 0
  await recordLearning({
    student_id: data.student_id,
    action: 'answer',
    resource_id: data.resource_id,
    topic: data.topic,
    score,
  })
  return {
    added_to_wrong_book: !data.is_correct,
    is_correct: data.is_correct,
    question_id: data.question_id,
  }
}

export async function regenerateEvaluation(data) {
  return client.post('/evaluate/start', data)
}

export async function previewPathAdjustment(evaluationId) {
  return client.post(`/evaluate/reports/${evaluationId}/path-adjustments/preview`)
}

export async function applyPathAdjustment(evaluationId) {
  return client.post(`/evaluate/reports/${evaluationId}/path-adjustments/apply`)
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
