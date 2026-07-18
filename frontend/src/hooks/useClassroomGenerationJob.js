import { useCallback, useEffect, useState } from 'react'
import { generateClassroom, getJob } from '../services/classroomService'

export function useClassroomGenerationJob() {
  const [job, setJob] = useState(null)
  const [result, setResult] = useState(null)

  const start = useCallback(async (payload) => {
    const task = await generateClassroom(payload)
    setJob(task)
    return task
  }, [])

  useEffect(() => {
    if (!job?.task_id || job.status === 'done' || job.status === 'failed') return
    const timer = window.setInterval(async () => {
      const next = await getJob(job.task_id).catch(() => null)
      if (!next) return
      setJob(next)
      if (next.status === 'done') setResult(next.result)
    }, 1200)
    return () => window.clearInterval(timer)
  }, [job])

  return { job, result, start }
}
