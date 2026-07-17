import { useCallback, useState } from 'react'
import { message } from 'antd'
import { initializeCourseLearning } from '../services/orchestratorService'
import { useAgentJob } from './useAgentJob'
import { useAgentJobEvents } from './useAgentJobEvents'

export function useInitializeCourseLearning({ courseId, studentId, goal }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { job, resetJob, applyEvent } = useAgentJob()
  const handleEvent = useAgentJobEvents(applyEvent)

  const start = useCallback(async () => {
    if (!studentId) return null
    setLoading(true)
    setError(null)
    resetJob()
    try {
      const path = await initializeCourseLearning({
        studentId,
        goal,
        onEvent: handleEvent,
      })
      setResult({ courseId, path })
      message.success('学习路径已生成')
      return path
    } catch (err) {
      setError(err)
      handleEvent({ type: 'error', step: 'planner', message: err.message || '生成失败' })
      message.error(err.message || '生成失败')
      return null
    } finally {
      setLoading(false)
    }
  }, [courseId, goal, handleEvent, resetJob, studentId])

  return { start, loading, error, result, job }
}
