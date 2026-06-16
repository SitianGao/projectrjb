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
  const response = await fetch('/api/resources/generate/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
