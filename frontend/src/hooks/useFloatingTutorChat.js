import { useState, useCallback, useRef, useEffect } from 'react'
import { streamTutorChat } from '../services/aiWorkspaceService'

/**
 * Chat state hook for the floating AI tutor.
 * Wraps streamTutorChat with context-aware message injection
 * and personalized quick questions.
 */
export default function useFloatingTutorChat({
  studentId,
  courseId,
  stageId,
  taskId,
  courseTitle,
  stageTitle,
  taskTitle,
  topic,
  learningGoal,
  profileData, // { weaknesses: [], knowledge_level: '', learning_style: '' }
}) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const abortRef = useRef(null)

  // scroll to bottom on new messages
  useEffect(() => {
    // caller handles scroll
  }, [messages])

  function buildContext(extraHint = '') {
    let ctx = ''

    if (courseTitle) ctx += `当前课程：${courseTitle}\n`
    if (stageTitle) ctx += `当前阶段：${stageTitle}\n`
    if (taskTitle || topic) ctx += `当前学习内容：${taskTitle || topic}\n`

    // personalization
    if (profileData) {
      const weak = profileData.weaknesses || profileData.weakness
      if (Array.isArray(weak) && weak.length > 0) {
        ctx += `学生薄弱点：${weak.join('、')}\n`
      }
      if (profileData.knowledge_level) {
        ctx += `学生当前水平：${profileData.knowledge_level}\n`
      }
      if (profileData.learning_style) {
        ctx += `学生适合的学习方式：${profileData.learning_style}\n`
      }
    }
    if (extraHint) ctx += extraHint
    return ctx.trim()
  }

  const sendMessage = useCallback((text, opts = {}) => {
    const { selectedText, isQuickAction } = opts
    if (!text?.trim() || loading) return

    let fullMessage = buildContext()
    if (fullMessage) fullMessage += '\n\n'
    fullMessage += `学生问题：${text}`

    setLoading(true)
    const userMsg = { id: Date.now(), role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])

    let assistantContent = ''
    const assistantMsg = { id: Date.now() + 1, role: 'assistant', content: '' }
    setMessages((prev) => [...prev, assistantMsg])

    const controller = new AbortController()
    abortRef.current = controller

    streamTutorChat({
      studentId,
      message: fullMessage,
      courseId,
      stageId,
      taskId,
      learningGoal,
      action: 'ask',
      selectedText: selectedText || undefined,
      history: messages.slice(-6).map((m) => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: typeof m.content === 'string' ? m.content.slice(0, 500) : '',
      })),
      onToken: (token) => {
        assistantContent += token
        setMessages((prev) => {
          const copy = [...prev]
          const last = copy[copy.length - 1]
          if (last?.role === 'assistant') {
            copy[copy.length - 1] = { ...last, content: assistantContent }
          }
          return copy
        })
      },
      onEvent: (event) => {
        if (event?.type === 'error') {
          setMessages((prev) => {
            const copy = [...prev]
            const last = copy[copy.length - 1]
            if (last?.role === 'assistant') {
              copy[copy.length - 1] = {
                ...last,
                content: assistantContent || `抱歉，请求失败：${event.message || '未知错误'}`,
              }
            }
            return copy
          })
        }
      },
      onError: () => {
        setMessages((prev) => {
          const copy = [...prev]
          const last = copy[copy.length - 1]
          if (last?.role === 'assistant' && !assistantContent) {
            copy[copy.length - 1] = { ...last, content: '抱歉，请求失败，请稍后重试。' }
          }
          return copy
        })
      },
    }).finally(() => {
      setLoading(false)
    })
  }, [studentId, courseId, stageId, taskId, learningGoal, buildContext, loading, messages])

  const abort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    loading,
    sendMessage,
    abort,
    clearMessages,
  }
}
