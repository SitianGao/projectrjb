import client from './client'

/**
 * 学习资源相关 API
 */

// 搜索/获取资源列表
export async function getResources(params) {
  return client.get('/resources', { params })
}

// 获取资源详情
export async function getResource(resourceId) {
  return client.get(`/resources/${resourceId}`)
}

// 生成学习资源
export async function generateResources(data) {
  return client.post('/resources/generate', data)
}

// 流式生成资源
export async function generateResourcesStream(data) {
  const token = localStorage.getItem('auth_token')
  const response = await fetch('/api/resources/generate/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response
}

// 获取资源类型列表（文档/题目/思维导图）
export async function getResourceTypes() {
  return client.get('/resources/types')
}

// 收藏/标记资源
export async function bookmarkResource(resourceId) {
  return client.post(`/resources/${resourceId}/bookmark`)
}

export async function updateResourceState(resourceId, data) {
  return client.patch(`/resources/${resourceId}/state`, data)
}

// 查询异步任务状态（轮询用）
export async function getTaskStatus(taskId) {
  return client.get(`/task/${taskId}/status`)
}

// ── PPT 生成相关 API ──

// 生成 PPT（异步任务）
export async function generatePpt(data) {
  return client.post('/ppt/generate', data, { timeout: 300000 }) // 5 分钟，PPT 生成需要较长时间
}

// 查询 PPT 生成状态
export async function getPptStatus(sid) {
  return client.get(`/ppt/status/${sid}`)
}

// 获取 PPT 资源详情
export async function getPptResource(resourceId) {
  return client.get(`/ppt/${resourceId}`)
}

// 下载 PPT 文件（返回下载 URL）
export function getPptDownloadUrl(resourceId) {
  return `/api/ppt/${resourceId}/download`
}

// 获取与当前学习任务精确绑定的资源和课程上下文
export async function getTaskResource(courseId, taskId, params = {}) {
  return client.get(
    `/resources/courses/${encodeURIComponent(courseId)}/tasks/${encodeURIComponent(taskId)}`,
    { params },
  )
}

// 按任务上下文生成资源；topic、阶段、难度均可由后端从任务推导
// LLM 生成 + RAG 检索可能耗时较长，单独放宽超时
export async function generateTaskResource(courseId, taskId, data = {}) {
  return client.post(
    `/resources/courses/${encodeURIComponent(courseId)}/tasks/${encodeURIComponent(taskId)}`,
    data,
    { timeout: 120000 }, // 2 分钟，LLM 生成需要较长时间
  )
}
