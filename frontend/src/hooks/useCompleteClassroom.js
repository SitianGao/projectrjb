import { useCallback, useState } from 'react'
import { completeClassroom } from '../services/classroomSessionService'

export function useCompleteClassroom(classroom, session) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const complete = useCallback(async () => {
    if (!classroom?.classroom_id || !session?.session_id) return null
    setLoading(true)
    try {
      const data = await completeClassroom(classroom.classroom_id, session.session_id)
      setResult(data)
      return data
    } finally {
      setLoading(false)
    }
  }, [classroom?.classroom_id, session?.session_id])
  return { complete, result, loading }
}
