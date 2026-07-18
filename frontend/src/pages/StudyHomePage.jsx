import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button, Empty, message, Result, Spin } from 'antd'
import { MessageOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  completeCourseTask,
  getCourseLearningContext,
} from '../api/courseLearning'
import { useAuth } from '../contexts/AuthContext'
import CourseContextHeader from '../components/CourseContextHeader'
import CourseTaskSidebar from '../components/CourseTaskSidebar'
import LearningContentPanel from '../components/LearningContentPanel'
import AITutorPanel from '../components/AITutorPanel'
import { InteractiveClassroomTaskContent } from './InteractiveClassroomPage'

// ── Main Component ──────────────────────────────────

export default function StudyHomePage() {
  const navigate = useNavigate()
  const { courseId, taskId } = useParams()
  const { activeCourse, courses, activateCourse } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [learningContext, setLearningContext] = useState(null)
  const [course, setCourse] = useState(activeCourse || null)
  const [completing, setCompleting] = useState(false)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      let targetCourse = courseId
        ? courses.find((item) => String(item.id) === String(courseId))
        : activeCourse

      if (courseId && (!activeCourse || String(activeCourse.id) !== String(courseId))) {
        targetCourse = await activateCourse(courseId)
      }

      if (!targetCourse?.id) {
        throw new Error('当前课程上下文不存在，请重新选择课程')
      }

      const context = await getCourseLearningContext(
        targetCourse.id,
        taskId ? decodeURIComponent(taskId) : null,
      )
      if (!context?.path?.stages?.length) {
        throw new Error('还没有生成学习路径，请先和 ChatBox 完成学习画像')
      }

      setCourse(targetCourse || activeCourse)
      setLearningContext(context)
    } catch (err) {
      setError(err.message || '学习页面加载失败')
    } finally {
      setLoading(false)
    }
  }, [activateCourse, activeCourse, courseId, courses, taskId])

  useEffect(() => {
    const timer = setTimeout(loadData, 0)
    return () => clearTimeout(timer)
  }, [loadData])

  // ── Derived data ──────────────────────────────────

  const pathData = learningContext?.path || null
  const currentStage = learningContext?.stage || null
  const tasksState = useMemo(() => learningContext?.tasks || [], [learningContext?.tasks])
  const currentTaskFromState = learningContext?.current_task || null
  const currentTaskId = currentTaskFromState?.task_id || currentTaskFromState?.id || null

  useEffect(() => {
    if (course?.id && currentTaskId && !taskId) {
      navigate(`/course/${course.id}/learn/${encodeURIComponent(currentTaskId)}`, { replace: true })
    }
  }, [course?.id, currentTaskId, navigate, taskId])

  const currentTaskIdx = useMemo(() => tasksState.findIndex((t) => t.id === currentTaskId), [tasksState, currentTaskId])
  const progress = learningContext?.progress || { completed: 0, total: 0, percent: 0 }

  const courseName = useMemo(() => {
    const raw = learningContext?.course?.name || course?.title || pathData?.goal || '当前课程'
    return String(raw).replace(/^学习|掌握/g, '').slice(0, 20) || '人工智能'
  }, [learningContext, pathData, course])

  const currentTopic = currentTaskFromState?.title || currentStage?.title || ''

  // ── Handlers ──────────────────────────────────────

  const handleSelectTask = useCallback((task) => {
    if (task.status === 'locked') return
    if (course?.id) {
      navigate(`/course/${course.id}/learn/${encodeURIComponent(task.id)}`)
    }
  }, [course, navigate])

  const handlePrev = useCallback(() => {
    if (currentTaskIdx > 0) {
      const prevTask = tasksState[currentTaskIdx - 1]
      if (course?.id) navigate(`/course/${course.id}/learn/${encodeURIComponent(prevTask.id)}`)
    }
  }, [course, currentTaskIdx, navigate, tasksState])

  const handleNext = useCallback(() => {
    if (currentTaskIdx < tasksState.length - 1) {
      const nextTask = tasksState[currentTaskIdx + 1]
      if (nextTask.status !== 'locked') {
        if (course?.id) navigate(`/course/${course.id}/learn/${encodeURIComponent(nextTask.id)}`)
      }
    }
  }, [course, currentTaskIdx, navigate, tasksState])

  const handleComplete = useCallback(async (task) => {
    setCompleting(true)
    try {
      const result = await completeCourseTask(course.id, task.task_id || task.id)
      message.success(result.idempotent ? '该任务已完成，进度保持不变' : '任务已完成，进度已保存')
      if (result.next_task?.task_id) {
        navigate(`/course/${course.id}/learn/${encodeURIComponent(result.next_task.task_id)}`)
      } else if (result.continue_target) {
        navigate(result.continue_target)
      } else {
        await loadData()
      }
    } catch (err) {
      message.error(err.message || '任务完成失败')
    } finally {
      setCompleting(false)
    }
  }, [course, loadData, navigate])

  // ── Render ────────────────────────────────────────

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', background: '#F6F7FB' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', background: '#F6F7FB', padding: 48 }}>
        <Result
          status="warning"
          title="还不能进入学习页面"
          subTitle={error}
          extra={[
            <Button key="chat" type="primary" icon={<MessageOutlined />} onClick={() => navigate('/profile', { state: { startChat: true } })}>
              返回 ChatBox
            </Button>,
            <Button key="reload" icon={<ReloadOutlined />} onClick={loadData}>重新加载</Button>,
          ]}
        />
      </div>
    )
  }

  if (!pathData || !learningContext) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', background: '#F6F7FB' }}>
        <Empty description="暂无学习数据" />
      </div>
    )
  }

  if (currentTaskFromState?.type === 'interactive_classroom') {
    return (
      <InteractiveClassroomTaskContent
        courseId={course?.id || courseId}
      />
    )
  }

  return (
    <div style={{
      minHeight: '100%',
      background: '#F6F7FB',
      padding: '16px 24px 32px',
    }}>
      <div style={{ maxWidth: 1280, margin: '0 auto' }}>
        <CourseContextHeader
          courseName={courseName}
          courseId={course?.id}
          stageTitle={currentStage?.title || '当前阶段'}
          stageDescription={currentStage?.description || ''}
          stageIndex={pathData?.current_stage || 1}
          completedTasks={progress.completed}
          totalTasks={progress.total}
        />

        <div style={{
          display: 'grid',
          gridTemplateColumns: '240px minmax(0, 1fr) 320px',
          gap: 16,
          alignItems: 'stretch',
        }}>
          <CourseTaskSidebar
            tasks={tasksState}
            currentTaskId={currentTaskId}
            onSelectTask={handleSelectTask}
          />

          <LearningContentPanel
            task={currentTaskFromState}
            taskIndex={currentTaskIdx}
            totalTasks={tasksState.length}
            onPrev={handlePrev}
            onNext={handleNext}
            onComplete={handleComplete}
            completing={completing}
          />

          <AITutorPanel
            currentTopic={currentTopic}
            currentContent={currentTaskFromState?.content}
          />
        </div>
      </div>
    </div>
  )
}
