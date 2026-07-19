import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import { useAuth } from '../contexts/AuthContext'
import { getCourseLearningState } from '../api/courseLearning'

/**
 * Unified "Continue Learning" logic.
 * All continue-learning buttons must use this hook.
 *
 * Resolution order:
 * 1. No course → /courses
 * The backend owns target resolution through continue_target.route.
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
      learningData = await getCourseLearningState(cid)
    } catch (error) {
      message.error(error.message || '学习状态加载失败')
      return
    }

    const targetRoute = learningData?.continue_target?.route
    if (targetRoute) {
      navigate(targetRoute)
      return
    }

    message.error('暂时没有可进入的学习内容')
  }, [activeCourse, courses, navigate])

  return { continueLearning: go }
}
