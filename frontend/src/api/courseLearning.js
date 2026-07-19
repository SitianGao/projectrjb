import client from './client'

export function getCourseLearningPath(courseId) {
  return client.get(`/courses/${encodeURIComponent(courseId)}/learning-path`)
}

export function getCourseLearningState(courseId) {
  return client.get(`/courses/${encodeURIComponent(courseId)}/learning-state`)
}

export function getCourseLearningContext(courseId, taskId) {
  const base = `/courses/${encodeURIComponent(courseId)}/learn`
  return client.get(taskId ? `${base}/${encodeURIComponent(taskId)}` : base)
}

export function completeCourseTask(courseId, taskId) {
  return client.post(
    `/courses/${encodeURIComponent(courseId)}/tasks/${encodeURIComponent(taskId)}/complete`,
  )
}

export function startStudySession(courseId, taskId) {
  return client.post(
    `/courses/${encodeURIComponent(courseId)}/study-sessions`,
    { task_id: taskId || null },
  )
}

export function closeStudySession(courseId, sessionId) {
  return client.post(
    `/courses/${encodeURIComponent(courseId)}/study-sessions/${encodeURIComponent(sessionId)}/close`,
  )
}

export function getPathGenerationSource(courseId) {
  return client.get(
    `/courses/${encodeURIComponent(courseId)}/learning-path/generation`,
  )
}
