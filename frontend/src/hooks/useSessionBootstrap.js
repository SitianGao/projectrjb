import { useCallback, useEffect, useState } from 'react'
import { getSessionBootstrap, resolveLoginTarget } from '../services/sessionService'

export function useSessionBootstrap({ auto = true } = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(auto)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const next = await getSessionBootstrap()
      setData(next)
      return next
    } catch (err) {
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!auto) return
    const timer = window.setTimeout(() => {
      refresh().catch(() => {})
    }, 0)
    return () => window.clearTimeout(timer)
  }, [auto, refresh])

  return {
    data,
    loading,
    error,
    refresh,
    loginTarget: resolveLoginTarget(data),
  }
}
