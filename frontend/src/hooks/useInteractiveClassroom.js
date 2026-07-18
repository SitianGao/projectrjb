import { useCallback, useEffect, useState } from 'react'
import { getClassroom, getDemoClassroom } from '../services/classroomService'

export function useInteractiveClassroom({ courseId, classroomId }) {
  const [classroom, setClassroom] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = classroomId ? await getClassroom(classroomId) : await getDemoClassroom(courseId)
      setClassroom(data)
      return data
    } catch (err) {
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [classroomId, courseId])

  useEffect(() => {
    const timer = window.setTimeout(() => { load().catch(() => {}) }, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  return { classroom, loading, error, reload: load }
}
