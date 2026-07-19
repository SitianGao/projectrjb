import { useCallback, useState } from 'react'
import { streamTutorChat } from '../services/aiWorkspaceService'

export function useChatStreaming({
  studentId,
  courseId,
  stageId,
  taskId,
  learningGoal,
  messages,
  setMessages,
}) {
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)

  const send = useCallback(async (content) => {
    const text = String(content || '').trim()
    if (!text || loading) return
    const userMessage = { role: 'user', content: text }
    const assistantMessage = { role: 'assistant', content: '' }
    const next = [...messages, userMessage, assistantMessage]
    setMessages(next)
    setLoading(true)
    try {
      let acc = ''
      await streamTutorChat({
        studentId,
        courseId,
        stageId,
        taskId,
        learningGoal,
        message: text,
        history: messages.map((item) => item.content),
        conversationId: sessionId,
        onToken: (token) => {
          acc += token
          setMessages([...messages, userMessage, { ...assistantMessage, content: acc || '正在整理回答...' }])
        },
        onEvent: (event) => {
          const nextSessionId = event?.session_id || event?.data?.session_id
          if (nextSessionId) setSessionId(nextSessionId)
        },
      })
    } finally {
      setLoading(false)
    }
  }, [
    courseId,
    learningGoal,
    loading,
    messages,
    setMessages,
    sessionId,
    stageId,
    studentId,
    taskId,
  ])

  return { send, loading, sessionId }
}
