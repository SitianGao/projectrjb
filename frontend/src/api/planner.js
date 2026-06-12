import client from './client'

/**
 * 学习规划相关 API
 */

// 流式生成学习路径 (SSE)
export async function generateLearningPathStream(data) {
  const response = await fetch('/api/planner/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response
}

// 非流式生成学习路径
export async function generateLearningPath(data) {
  return client.post('/planner/generate', data)
}

// 获取学生当前学习路径
export async function getStudentPaths(studentId) {
  return client.get(`/planner/${studentId}`)
}

// 更新学习路径节点状态 (暂未实现，预留)
export async function updatePathNode(pathId, nodeId, status) {
  return client.patch(`/planner/${pathId}/node/${nodeId}`, { status })
}
