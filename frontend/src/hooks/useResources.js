import { useState, useEffect, useCallback } from 'react'
import { getResources } from '../api/resource'
import { useAuth } from '../contexts/AuthContext'

/**
 * Unified resource fetching hook.
 * Supports course, stage, task, type, difficulty, keyword, pagination, sort.
 */
export function useResources(filters = {}) {
  const { studentId } = useAuth()
  const [data, setData] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = { student_id: studentId, page_size: 100 }
      if (filters.courseId) params.course_id = filters.courseId
      if (filters.stageId) params.stage_id = filters.stageId
      if (filters.type) params.type = filters.type
      if (filters.difficulty) params.difficulty = filters.difficulty
      if (filters.keyword) params.keyword = filters.keyword
      if (filters.page) params.page = filters.page
      if (filters.sort) params.sort = filters.sort

      const res = await getResources(params)
      setData(res?.items || res?.resources || [])
      setTotal(res?.total || 0)
    } catch (err) {
      setError(err.message || '加载资源失败')
    } finally {
      setLoading(false)
    }
  }, [studentId, JSON.stringify(filters)])

  useEffect(() => { load() }, [load])

  return { data, total, loading, error, reload: load }
}
