import { useCallback, useState } from 'react'
import { submitClassroomQuiz } from '../services/classroomSessionService'

export function useClassroomQuiz(classroom, session) {
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const submit = useCallback(async () => {
    if (!classroom?.classroom_id || !session?.session_id) return null
    const data = await submitClassroomQuiz(classroom.classroom_id, session.session_id, answers)
    setResult(data)
    return data
  }, [answers, classroom?.classroom_id, session?.session_id])
  return { answers, setAnswers, result, submit }
}
