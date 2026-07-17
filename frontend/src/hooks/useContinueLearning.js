import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import { useAuth } from '../contexts/AuthContext'
import { getLearningPath } from '../api/planner'
import { normalizeTasks } from '../utils/stageUtils'

/**
 * Unified "Continue Learning" logic.
 * All continue-learning buttons must use this hook.
 *
 * Resolution order:
 * 1. No course → /courses
 * 2. No learning path → /course/:id/path (prompt to generate)
 * 3. Current stage has in-progress task → /course/:id/learn/:taskId
 * 4. First pending task in current stage → /course/:id/learn/:taskId
 * 5. Stage complete, next stage unlocked → next stage first task
 * 6. All done → /course/:id/path
 */
export function useContinueLearning() {
  const navigate = useNavigate()
  const { activeCourse, courses, studentId } = useAuth()

  const go = useCallback(async (courseIdOverride) => {
    const course = courseIdOverride
      ? courses?.find((c) => String(c.id) === String(courseIdOverride))
      : activeCourse

    if (!course) {
      navigate('/courses')
      return
    }

    const cid = course.id
    const sid = course.student_id || studentId
    if (!sid) {
      navigate('/courses')
      return
    }

    let path
    try {
      path = await getLearningPath(sid)
    } catch {
      message.info('请先生成学习路径')
      navigate(`/course/${cid}/path`)
      return
    }

    if (!path?.stages?.length) {
      message.info('请先生成学习路径')
      navigate(`/course/${cid}/path`)
      return
    }

    const currentStageNum = path.current_stage || 1
    const currentStage = path.stages.find(
      (s) => Number(s.stage_id) === Number(currentStageNum),
    ) || path.stages[0]

    const tasks = normalizeTasks(currentStage?.tasks)
    const deduped = tasks.filter((t, i, arr) => {
      const key = t.id || t.task_id
      return key && arr.findIndex((x) => (x.id || x.task_id) === key) === i
    })

    // Find first incomplete task
    const activeTask = deduped.find((t) => t.status === 'active' || t.status === 'in_progress')
    if (activeTask) {
      const tid = activeTask.id || activeTask.task_id
      navigate(`/course/${cid}/learn/${tid}`)
      return
    }

    const firstPending = deduped.find((t) => !t.status || t.status === 'pending')
    if (firstPending) {
      const tid = firstPending.id || firstPending.task_id
      navigate(`/course/${cid}/learn/${tid}`)
      return
    }

    // All current stage tasks done — try next stage
    const nextStage = path.stages.find((s) => Number(s.stage_id) === Number(currentStageNum) + 1)
    if (nextStage) {
      const nextTasks = normalizeTasks(nextStage.tasks)
      const first = nextTasks[0]
      if (first) {
        const tid = first.id || first.task_id
        navigate(`/course/${cid}/learn/${tid}`)
        return
      }
    }

    // All done
    navigate(`/course/${cid}/path`)
  }, [activeCourse, courses, studentId, navigate])

  return { continueLearning: go }
}
