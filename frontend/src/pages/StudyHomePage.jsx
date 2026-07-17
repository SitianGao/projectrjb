import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button, Empty, message, Result, Spin } from 'antd'
import { MessageOutlined, ReloadOutlined } from '@ant-design/icons'
import { getLearningPath } from '../api/planner'
import { useAuth } from '../contexts/AuthContext'
import {
  buildStageLearningTasks,
  findCurrentLearningTask,
  getCurrentStage,
  getTasksProgress,
} from '../utils/courseLearning'
import CourseContextHeader from '../components/CourseContextHeader'
import CourseTaskSidebar from '../components/CourseTaskSidebar'
import LearningContentPanel from '../components/LearningContentPanel'
import AITutorPanel from '../components/AITutorPanel'

// ── Main Component ──────────────────────────────────

export default function StudyHomePage() {
  const navigate = useNavigate()
  const { courseId, taskId } = useParams()
  const { studentId, activeCourse, courses, activateCourse } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pathData, setPathData] = useState(null)
  const [course, setCourse] = useState(activeCourse || null)
  const [taskOverrides, setTaskOverrides] = useState({})
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

      if (!targetCourse?.student_id && !studentId) {
        throw new Error('当前课程上下文不存在，请重新选择课程')
      }

      const targetStudentId = targetCourse?.student_id || studentId
      const path = await getLearningPath(targetStudentId)

      if (!path?.stages?.length) {
        throw new Error('还没有生成学习路径，请先和 ChatBox 完成学习画像')
      }

      setCourse(targetCourse || activeCourse)
      setPathData(path)
    } catch (err) {
      setError(err.message || '学习页面加载失败')
    } finally {
      setLoading(false)
    }
  }, [activateCourse, activeCourse, courseId, courses, studentId])

  useEffect(() => {
    const timer = setTimeout(loadData, 0)
    return () => clearTimeout(timer)
  }, [loadData])

  // ── Derived data ──────────────────────────────────

  const currentStage = useMemo(() => getCurrentStage(pathData), [pathData])

  const tasks = useMemo(() => buildStageLearningTasks(currentStage), [currentStage])

  const tasksState = useMemo(() => (
    tasks.map((task) => ({ ...task, ...(taskOverrides[task.id] || {}) }))
  ), [taskOverrides, tasks])

  const currentTaskId = useMemo(() => {
    if (!tasksState.length) return null
    const requestedTaskId = taskId ? decodeURIComponent(taskId) : null
    if (requestedTaskId && tasksState.some((task) => task.id === requestedTaskId)) return requestedTaskId
    return (findCurrentLearningTask(tasksState) || tasksState[0])?.id || null
  }, [taskId, tasksState])

  useEffect(() => {
    if (course?.id && currentTaskId && taskId !== currentTaskId) {
      navigate(`/course/${course.id}/learn/${encodeURIComponent(currentTaskId)}`, { replace: true })
    }
  }, [course?.id, currentTaskId, navigate, taskId])

  const currentTaskFromState = useMemo(() => tasksState.find((t) => t.id === currentTaskId) || null, [tasksState, currentTaskId])
  const currentTaskIdx = useMemo(() => tasksState.findIndex((t) => t.id === currentTaskId), [tasksState, currentTaskId])
  const progress = useMemo(() => getTasksProgress(tasksState), [tasksState])

  const courseName = useMemo(() => {
    const raw = pathData?.goal || course?.title || '人工智能'
    return String(raw).replace(/^学习|掌握/g, '').slice(0, 20) || '人工智能'
  }, [pathData, course])

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
    await new Promise((r) => setTimeout(r, 500))

    const idx = tasksState.findIndex((t) => t.id === task.id)
    const next = idx >= 0 ? tasksState[idx + 1] : null
    setTaskOverrides((prev) => {
      const nextOverrides = { ...prev, [task.id]: { status: 'completed' } }
      tasksState.forEach((item, index) => {
        if (index !== idx && item.status === 'active') {
          nextOverrides[item.id] = { ...(nextOverrides[item.id] || {}), status: 'pending' }
        }
      })
      if (next) nextOverrides[next.id] = { ...(nextOverrides[next.id] || {}), status: 'active' }
      return nextOverrides
    })

    if (idx < tasksState.length - 1) {
      if (course?.id) navigate(`/course/${course.id}/learn/${encodeURIComponent(next.id)}`)
    }
    setCompleting(false)
  }, [course, navigate, tasksState])

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

  if (!pathData) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', background: '#F6F7FB' }}>
        <Empty description="暂无学习数据" />
      </div>
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
            onSave={async (t) => { message.success('进度已保存') }}
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
