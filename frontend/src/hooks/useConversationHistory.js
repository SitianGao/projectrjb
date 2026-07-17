import { useMemo, useState } from 'react'

export function useConversationHistory(courseId) {
  const key = `aiWorkspaceHistory:${courseId || 'global'}`
  const initial = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem(key) || '[]')
    } catch {
      return []
    }
  }, [key])
  const [messages, setMessages] = useState(initial)

  const saveMessages = (next) => {
    setMessages(next)
    localStorage.setItem(key, JSON.stringify(next.slice(-40)))
  }

  return { messages, setMessages: saveMessages }
}
