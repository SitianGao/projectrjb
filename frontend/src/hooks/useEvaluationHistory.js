import { useCallback, useEffect, useState } from 'react'
import { fetchEvaluationHistory } from '../services/evaluationService'

export default function useEvaluationHistory({ studentId, courseId }) {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    if (!studentId || !courseId) return
    setLoading(true)
    try {
      setHistory(await fetchEvaluationHistory({ studentId, courseId }))
    } catch {
      setHistory([])
    } finally {
      setLoading(false)
    }
  }, [courseId, studentId])

  useEffect(() => {
    const timer = setTimeout(reload, 0)
    return () => clearTimeout(timer)
  }, [reload])

  return { history, loading, reload }
}
