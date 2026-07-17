import { useCallback, useEffect, useState } from 'react'
import { getCourseProfile } from '../services/courseProfileService'

export function useLiveCourseProfile(courseId) {
  const [profileState, setProfileState] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    if (!courseId) return null
    setLoading(true)
    try {
      const data = await getCourseProfile(courseId)
      setProfileState(data)
      return data
    } finally {
      setLoading(false)
    }
  }, [courseId])

  const applyProfileResult = useCallback((result) => {
    setProfileState((prev) => ({ ...(prev || {}), ...(result || {}) }))
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refresh().catch(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  return { profileState, loading, refresh, applyProfileResult }
}
