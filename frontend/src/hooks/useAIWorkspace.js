import { useLocation, useParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useConversationHistory } from './useConversationHistory'
import { useChatStreaming } from './useChatStreaming'

export function useAIWorkspace() {
  const { courseId } = useParams()
  const location = useLocation()
  const { activeCourse, courses, studentId } = useAuth()
  const scopedCourseId = courseId || activeCourse?.id
  const scopedCourse = courses.find(
    (item) => String(item.id) === String(scopedCourseId),
  ) || activeCourse
  const scopedStudentId = scopedCourse?.student_id || studentId
  const routeContext = location.state || {}
  const history = useConversationHistory(scopedCourseId)
  const chat = useChatStreaming({
    studentId: scopedStudentId,
    courseId: scopedCourseId,
    stageId: routeContext.stage_id,
    taskId: routeContext.task_id,
    learningGoal: routeContext.learning_goal || scopedCourse?.goal,
    messages: history.messages,
    setMessages: history.setMessages,
  })

  return {
    courseId: scopedCourseId,
    studentId: scopedStudentId,
    course: scopedCourse,
    messages: history.messages,
    send: chat.send,
    loading: chat.loading,
    sessionId: chat.sessionId,
  }
}
