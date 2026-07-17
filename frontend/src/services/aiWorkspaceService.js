import { authFetch } from '../api/authFetch'
import client from '../api/client'

export async function streamTutorChat({ studentId, message, history = [], onToken }) {
  const response = await authFetch('/api/tutor/ask/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: studentId, message, history, explanation_style: 'auto' }),
  })
  if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const raw = line.slice(6).trim()
      if (!raw || raw === '[DONE]') continue
      try {
        const event = JSON.parse(raw)
        if (event.type === 'chat' || event.type === 'delta') onToken?.(event.content || event.delta || '')
        if (event.type === 'error') throw new Error(event.message || 'AI 导师回复失败')
      } catch {
        onToken?.('')
      }
    }
  }
}

export async function createResourceJob(payload) {
  return client.post('/resource/generate', payload)
}

export async function getTaskStatus(taskId) {
  return client.get(`/task/${taskId}/status`)
}
