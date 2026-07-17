import { useCallback, useEffect, useState } from 'react'
import { fetchEvaluationReport } from '../services/evaluationService'

export default function useEvaluationReport({ studentId, courseId, scope, stageId, reportId }) {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const reload = useCallback(async () => {
    if (!studentId && !reportId) return
    if (!courseId && !reportId) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetchEvaluationReport({ studentId, courseId, scope, stageId, reportId })
      setReport(data)
    } catch (err) {
      setError(err.message || '评估报告加载失败')
    } finally {
      setLoading(false)
    }
  }, [courseId, reportId, scope, stageId, studentId])

  useEffect(() => {
    const timer = setTimeout(reload, 0)
    return () => clearTimeout(timer)
  }, [reload])

  return { report, setReport, loading, error, reload }
}
