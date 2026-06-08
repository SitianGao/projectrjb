import client from './client'

/**
 * 学习规划相关 API
 */

// 生成学习路径
export async function generateLearningPath(data) {
  return client.post('/planner/path', data)
}

// 获取学习路径
export async function getLearningPath(pathId) {
  return client.get(`/planner/path/${pathId}`)
}

// 获取学生的所有学习路径
export async function getStudentPaths(studentId) {
  return client.get(`/planner/paths`, { params: { student_id: studentId } })
}

// 流式生成学习路径
export async function generateLearningPathStream(data) {
  const response = await fetch('/api/planner/path/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response
}

// 更新学习路径节点状态
export async function updatePathNode(pathId, nodeId, status) {
  return client.patch(`/planner/path/${pathId}/node/${nodeId}`, { status })
}
