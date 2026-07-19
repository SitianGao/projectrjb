import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { message } from 'antd'
import { sendCourseProfileMessage } from '../services/profileConversationService'
import {
  getCourseProfileConversationState,
  getCurrentCourseProfileConversation,
} from '../services/courseProfileService'

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

export function useProfileConversation(courseId, { onProfileResult, initialConversationId } = {}) {
  const stored = useMemo(() => readStored(courseId), [courseId])
  const [conversationId, setConversationId] = useState(() => (
    initialConversationId || stored?.conversationId || null
  ))
  const [messages, setMessages] = useState(stored?.messages || [])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const pendingRef = useRef(false)

  const persist = useCallback((nextMessages) => {
    if (!courseId || !conversationId) return
    sessionStorage.setItem(storageKey(courseId), JSON.stringify({ conversationId, messages: nextMessages }))
  }, [conversationId, courseId])

  const mergeMessages = useCallback((incoming) => {
    const seen = new Set()
    const merged = []
    for (const item of incoming || []) {
      const key = item.id || `${item.role}:${item.client_message_id || ''}:${item.content}`
      if (seen.has(key)) continue
      seen.add(key)
      merged.push(item)
    }
    return merged
  }, [])

  useEffect(() => {
    if (!courseId || conversationId) return undefined
    let cancelled = false
    getCurrentCourseProfileConversation(courseId)
      .then((current) => {
        if (!cancelled) setConversationId(current?.conversation_id || `profile-${courseId}-draft`)
      })
      .catch((err) => {
        if (!cancelled) {
          setConversationId(`profile-${courseId}-draft`)
          setError(err)
        }
      })
    return () => { cancelled = true }
  }, [conversationId, courseId])

  useEffect(() => {
    if (!courseId || !conversationId) return undefined
    let cancelled = false
    getCourseProfileConversationState(courseId, conversationId)
      .then((state) => {
        if (cancelled) return
        if (state?.messages?.length) {
          const next = mergeMessages(state.messages)
          setMessages(next)
          persist(next)
        }
        onProfileResult?.(state)
      })
      .catch((err) => setError(err))
    return () => { cancelled = true }
  }, [conversationId, courseId, mergeMessages, onProfileResult, persist])

  const send = useCallback(async (content) => {
    const text = String(content || '').trim()
    if (!text || loading || pendingRef.current) return
    if (!courseId || !conversationId) {
      message.error('画像会话正在恢复，请稍后重试')
      return
    }
    pendingRef.current = true
    const clientMessageId = `cm-${Date.now()}-${Math.random().toString(16).slice(2)}`
    const optimisticMessage = {
      id: `local:${clientMessageId}`,
      client_message_id: clientMessageId,
      role: 'user',
      content: text,
      pending: true,
    }
    const nextMessages = mergeMessages([...messages, optimisticMessage])
    setMessages(nextMessages)
    persist(nextMessages)
    setLoading(true)
    setError(null)
    try {
      const result = await sendCourseProfileMessage(courseId, conversationId, {
        client_message_id: clientMessageId,
        message: text,
      })
      const confirmedUser = {
        ...optimisticMessage,
        id: result.message_id || optimisticMessage.id,
        pending: false,
      }
      const assistant = {
        ...(result.assistant_message || {}),
        id: result.message_id ? `${result.message_id}:assistant` : `assistant:${clientMessageId}`,
        client_message_id: clientMessageId,
        role: 'assistant',
        agent_run: result.agent_run || result.assistant_message?.agent_run,
      }
      const withoutLocal = nextMessages.filter((item) => item.id !== optimisticMessage.id)
      const withReply = mergeMessages([...withoutLocal, confirmedUser, assistant])
      setMessages(withReply)
      persist(withReply)
      onProfileResult?.(result)
    } catch (err) {
      setError(err)
      message.error(err.message || '画像对话失败')
    } finally {
      pendingRef.current = false
      setLoading(false)
    }
  }, [conversationId, courseId, loading, mergeMessages, messages, onProfileResult, persist])

  return { conversationId, messages, loading, error, send }
}
