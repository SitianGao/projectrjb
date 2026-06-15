import client from './client'

/**
 * 学习资源相关 API
 *
 * 后端端点：
 *   POST /api/resource/generate    生成学习资源
 *   GET  /api/resource/{id}        获取资源详情
 *   GET  /api/resource/list        资源列表
 */

// 获取资源列表
export async function getResources(params) {
  return client.get('/resource/list', { params })
}

// 获取资源详情
export async function getResource(resourceId) {
  return client.get(`/resource/${resourceId}`)
}

// 生成学习资源
export async function generateResources(data) {
  return client.post('/resource/generate', data)
}

// 流式生成资源 (SSE)
export async function generateResourcesStream(data) {
  const response = await fetch('/api/resource/generate/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response
}

// 获取资源类型列表
export async function getResourceTypes() {
  return client.get('/resource/types')
}

// 收藏/标记资源
export async function bookmarkResource(resourceId) {
  return client.post(`/resource/${resourceId}/bookmark`)
}
