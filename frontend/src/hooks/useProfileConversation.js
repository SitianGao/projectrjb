import { useCallback, useMemo, useState } from 'react'
import { message } from 'antd'
import { sendCourseProfileMessage } from '../services/profileConversationService'

function storageKey(courseId) {
  return `courseProfileConversation:${courseId}`
}

function readStored(courseId) {
  try {
    return JSON.parse(sessionStorage.getItem(storageKey(courseId)) || 'null')
  } catch {
    return null
  }
}

export function useProfileConversation(courseId, { onProfileResult } = {}) {
  const stored = useMemo(() => readStored(courseId), [courseId])
  const [conversationId] = useState(() => stored?.conversationId || `profile-${courseId || 'new'}-draft`)
  const [messages, setMessages] = useState(stored?.messages || [{
    role: 'assistant',
    content: '先聊聊这门课：你想学什么、现在基础怎样、每天大概能投入多久？我会在右侧实时更新课程画像。',
  }])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const persist = useCallback((nextMessages) => {
    if (!courseId) return
    sessionStorage.setItem(storageKey(courseId), JSON.stringify({ conversationId, messages: nextMessages }))
  }, [conversationId, courseId])

  const send = useCallback(async (content) => {
    const text = String(content || '').trim()
    if (!text || loading) return
    const nextMessages = [...messages, { role: 'user', content: text }]
    setMessages(nextMessages)
    persist(nextMessages)
    setLoading(true)
    setError(null)
    try {
      const result = await sendCourseProfileMessage(courseId, conversationId, {
        message: text,
        history: nextMessages,
      })
      const withReply = [...nextMessages, result.assistant_message]
      setMessages(withReply)
      persist(withReply)
      onProfileResult?.(result)
    } catch (err) {
      setError(err)
      message.error(err.message || '画像对话失败')
    } finally {
      setLoading(false)
    }
  }, [conversationId, courseId, loading, messages, onProfileResult, persist])

  return { conversationId, messages, loading, error, send }
}
