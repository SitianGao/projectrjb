import { useState, useEffect, useCallback } from 'react'
import { getResources } from '../api/resource'

/**
 * Unified resource fetching hook.
 * Supports course, stage, task, type, difficulty, keyword, pagination, sort.
 */
export function useResources(filters = {}) {
  const [data, setData] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = { page_size: 100 }
      if (filters.courseId) params.course_id = filters.courseId
      if (filters.stageId) params.stage_id = filters.stageId
      if (filters.type) params.type = filters.type
      if (filters.difficulty) params.difficulty = filters.difficulty
      if (filters.keyword) params.keyword = filters.keyword
      if (filters.page) params.page = filters.page
      if (filters.sort) params.sort = filters.sort
      if (filters.generationSource) params.generation_source = filters.generationSource
      if (filters.triggerSource) params.trigger_source = filters.triggerSource
      if (filters.learningStatus) params.learning_status = filters.learningStatus
      if (filters.favorite != null) params.favorite = filters.favorite
      if (filters.createdFrom) params.created_from = filters.createdFrom
      if (filters.createdTo) params.created_to = filters.createdTo

      const res = await getResources(params)
      setData(res?.items || res?.resources || [])
      setTotal(res?.total || 0)
    } catch (err) {
      setError(err.message || '加载资源失败')
    } finally {
      setLoading(false)
    }
  }, [
    filters.courseId,
    filters.stageId,
    filters.type,
    filters.difficulty,
    filters.keyword,
    filters.page,
    filters.sort,
    filters.generationSource,
    filters.triggerSource,
    filters.learningStatus,
    filters.favorite,
    filters.createdFrom,
    filters.createdTo,
  ])

  useEffect(() => {
    const timer = window.setTimeout(load, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  return { data, total, loading, error, reload: load }
}
