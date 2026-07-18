import { useCallback, useState } from 'react'
import { message } from 'antd'
import { askClassroomTutor } from '../services/classroomTutorService'

export function useClassroomTutor(classroom, session, currentScene) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const ask = useCallback(async (question, extra = {}) => {
    if (!classroom?.classroom_id || !session?.session_id) return
    const userMessage = { role: 'user', content: question }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)
    try {
      const result = await askClassroomTutor(classroom.classroom_id, session.session_id, {
        scene_id: currentScene?.scene_id,
        question,
        ...extra,
      })
      setMessages((prev) => [...prev, { role: 'assistant', content: result.answer, meta: result }])
      return result
    } catch (error) {
      message.warning('AI 导师暂时不可用，你仍可继续完成当前课堂')
      setMessages((prev) => [...prev, { role: 'assistant', content: 'AI 导师暂时不可用，你仍可继续完成当前课堂。' }])
      return null
    } finally {
      setLoading(false)
    }
  }, [classroom?.classroom_id, currentScene?.scene_id, session?.session_id])

  return { messages, loading, ask }
}
