import { useCallback, useState } from 'react'
import { streamTutorChat } from '../services/aiWorkspaceService'

export function useChatStreaming({ studentId, messages, setMessages }) {
  const [loading, setLoading] = useState(false)

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
        message: text,
        history: messages.map((item) => item.content),
        onToken: (token) => {
          acc += token
          setMessages([...messages, userMessage, { ...assistantMessage, content: acc || '正在整理回答...' }])
        },
      })
    } finally {
      setLoading(false)
    }
  }, [loading, messages, setMessages, studentId])

  return { send, loading }
}
