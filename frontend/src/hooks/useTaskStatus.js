import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * 异步任务轮询 Hook
 *
 * 用于轮询后端异步任务状态（生成画像/规划/资源/评估等）。
 *
 * @param {Function} fetchStatus - (taskId: string) => Promise<{status, result, error}>
 * @param {Object} options
 * @param {number} options.interval - 轮询间隔 ms，默认 2000
 * @returns {{
 *   taskId: string|null,
 *   status: 'idle'|'pending'|'running'|'completed'|'failed',
 *   result: any,
 *   error: string|null,
 *   startPolling: (taskId: string) => void,
 *   reset: () => void,
 * }}
 */
export function useTaskStatus(fetchStatus, { interval = 2000 } = {}) {
  const [taskId, setTaskId] = useState(null)
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const timerRef = useRef(null)
  const fetchRef = useRef(fetchStatus)
  fetchRef.current = fetchStatus

  const poll = useCallback(
    async (id) => {
      try {
        const data = await fetchRef.current(id)
        setStatus(data.status)

        if (data.status === 'completed') {
          setResult(data.result)
          setError(null)
          return // 停止轮询
        }
        if (data.status === 'failed') {
          setError(data.error || '任务失败')
          return // 停止轮询
        }

        // pending / running：继续轮询
        timerRef.current = setTimeout(() => poll(id), interval)
      } catch (err) {
        setError(err.message || '查询任务状态失败')
        setStatus('failed')
      }
    },
    [interval],
  )

  const startPolling = useCallback(
    (id) => {
      reset()
      setTaskId(id)
      setStatus('pending')
      timerRef.current = setTimeout(() => poll(id), interval)
    },
    [poll],
  )

  const reset = useCallback(() => {
    clearTimeout(timerRef.current)
    timerRef.current = null
    setTaskId(null)
    setStatus('idle')
    setResult(null)
    setError(null)
  }, [])

  // 组件卸载时清理定时器
  useEffect(() => {
    return () => clearTimeout(timerRef.current)
  }, [])

  return { taskId, status, result, error, startPolling, reset }
}
