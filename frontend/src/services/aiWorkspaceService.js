import { authFetch } from '../api/authFetch'
import client from '../api/client'
import { streamSse } from '../utils/sseClient'

/**
 * Unified SSE tutor chat (delegates to streamSse).
 *
 * SSE event types supported: start | delta | progress | data | error | done
 */
export async function streamTutorChat({
  studentId,
  message,
  courseId,
  stageId,
  taskId,
  learningGoal,
  action = 'ask',
  selectedText,
  history = [],
  conversationId,
  onToken,
  onEvent,
}) {
  const payload = {
    student_id: studentId,
    message,
    history,
    explanation_style: 'auto',
  }

  if (courseId) payload.course_id = courseId
  if (stageId) payload.stage_id = stageId
  if (taskId) payload.task_id = taskId
  if (learningGoal) payload.learning_goal = learningGoal
  if (action) payload.action = action
  if (selectedText) payload.selected_text = selectedText
  if (conversationId) payload.conversation_id = conversationId

  const response = await authFetch('/api/tutor/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok || !response.body) {
    const err = new Error(`HTTP ${response.status}`)
    err.code = response.status === 401 ? 'TUTOR_AGENT_UNAVAILABLE'
      : response.status === 504 ? 'TUTOR_REQUEST_TIMEOUT'
      : 'TUTOR_LLM_FAILED'
    throw err
  }

  await streamSse(Promise.resolve(response), {
    onDelta: (text) => onToken?.(text),
    onData: (event) => onEvent?.(event),
    onError: (err) => {
      onEvent?.({ type: 'error', code: err.code, message: err.message })
      throw err
    },
    onDone: () => onEvent?.({ type: 'done' }),
  })
}

export async function createResourceJob(payload) {
  return client.post('/resource/generate', payload)
}

export async function createTutorResource(payload) {
  return client.post('/tutor/resources', payload)
}

export async function getTaskStatus(taskId) {
  return client.get(`/task/${taskId}/status`)
}
