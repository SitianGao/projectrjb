import { useCallback, useEffect, useState } from 'react'
import { createClassroomSession } from '../services/classroomSessionService'

export function useClassroomSession(classroomId) {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(false)

  const start = useCallback(async () => {
    if (!classroomId) return null
    setLoading(true)
    try {
      const data = await createClassroomSession(classroomId)
      setSession(data)
      return data
    } finally {
      setLoading(false)
    }
  }, [classroomId])

  useEffect(() => {
    const timer = window.setTimeout(() => { start().catch(() => {}) }, 0)
    return () => window.clearTimeout(timer)
  }, [start])

  return { session, setSession, loading, start }
}
