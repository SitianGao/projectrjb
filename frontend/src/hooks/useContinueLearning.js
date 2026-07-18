import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import { useAuth } from '../contexts/AuthContext'
import { getCourseLearningPath } from '../api/courseLearning'

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
  const { activeCourse, courses } = useAuth()

  const go = useCallback(async (courseIdOverride) => {
    const course = courseIdOverride
      ? courses?.find((c) => String(c.id) === String(courseIdOverride))
      : activeCourse

    if (!course) {
      navigate('/courses')
      return
    }

    const cid = course.id
    let learningData
    try {
      learningData = await getCourseLearningPath(cid)
    } catch {
      message.info('请先生成学习路径')
      navigate(`/course/${cid}/path`)
      return
    }

    if (!learningData?.path?.stages?.length) {
      message.info('请先生成学习路径')
      navigate(`/course/${cid}/path`)
      return
    }

    const targetRoute = learningData?.continue_target?.route
    if (targetRoute) {
      navigate(targetRoute)
      return
    }

    navigate(`/course/${cid}/path`)
  }, [activeCourse, courses, navigate])

  return { continueLearning: go }
}
