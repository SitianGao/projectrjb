import { useCallback, useState } from 'react'
import { createLocalAgentJob, reduceAgentJob } from '../services/agentJobService'

export function useAgentJob() {
  const [job, setJob] = useState(() => createLocalAgentJob())

  const resetJob = useCallback(() => {
    setJob(createLocalAgentJob())
  }, [])

  const applyEvent = useCallback((event) => {
    setJob((prev) => reduceAgentJob(prev, event))
  }, [])

  return { job, resetJob, applyEvent }
}
