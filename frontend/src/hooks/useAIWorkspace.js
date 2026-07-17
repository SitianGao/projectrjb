import { useParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useConversationHistory } from './useConversationHistory'
import { useChatStreaming } from './useChatStreaming'

export function useAIWorkspace() {
  const { courseId } = useParams()
  const { activeCourse, studentId } = useAuth()
  const scopedCourseId = courseId || activeCourse?.id
  const scopedStudentId = activeCourse?.student_id || studentId
  const history = useConversationHistory(scopedCourseId)
  const chat = useChatStreaming({
    studentId: scopedStudentId,
    messages: history.messages,
    setMessages: history.setMessages,
  })

  return {
    courseId: scopedCourseId,
    studentId: scopedStudentId,
    course: activeCourse,
    messages: history.messages,
    send: chat.send,
    loading: chat.loading,
  }
}
