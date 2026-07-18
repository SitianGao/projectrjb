import { useCallback, useRef, useState } from 'react'
import { checkTutorIntervention } from '../services/classroomTutorService'

export function useTutorIntervention(classroom, session) {
  const [intervention, setIntervention] = useState(null)
  const lastAtRef = useRef(0)

  const check = useCallback(async (sceneId, userActions) => {
    const now = Date.now()
    if (now - lastAtRef.current < 45000) return null
    if (!classroom?.classroom_id || !session?.session_id) return null
    const result = await checkTutorIntervention(classroom.classroom_id, session.session_id, {
      scene_id: sceneId,
      user_actions: userActions,
    }).catch(() => null)
    if (result?.should_intervene) {
      lastAtRef.current = now
      setIntervention(result)
    }
    return result
  }, [classroom?.classroom_id, session?.session_id])

  return { intervention, setIntervention, check }
}
