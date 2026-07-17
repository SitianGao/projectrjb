import client from './client'

/**
 * 获取课程首页聚合数据（课程信息 + 路径 + 进度 + 派生状态）。
 *
 * GET /api/auth/courses/:courseId/dashboard
 *
 * @param {string} courseId
 * @returns {Promise<{
 *   course: { id, student_id, name, goal, status },
 *   progress: { percentage, completed_tasks, total_tasks, learning_minutes, accuracy, streak_days },
 *   current_stage: { stage_id, title, description, objectives, topics } | null,
 *   current_task: { task_id, type, description, difficulty } | null,
 * }>}
 */
export async function getCourseDashboard(courseId) {
  return client.get(`/auth/courses/${courseId}/dashboard`)
}
