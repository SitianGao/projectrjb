import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Avatar, Button, Card, Empty, Progress, Skeleton, Space, Typography, message } from 'antd'
import {
  ArrowRightOutlined,
  BookOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  ProfileOutlined,
  RightOutlined,
} from '@ant-design/icons'
import { getLearningPath } from '../api/planner'
import { useAuth } from '../contexts/AuthContext'
import { getCurrentLearningTarget, getPathProgress } from '../utils/courseLearning'
import './CourseEntryPage.css'

const { Title, Text, Paragraph } = Typography

function isMeaningfulCourse(course) {
  const title = String(course?.title || '').trim().toLowerCase()
  if (!title) return false
  if (title === 'shux' || title === 'vjg') return false
  if (/^待命名课程/.test(course.title || '')) return false
  return true
}

function normalizeCourses(courses = []) {
  const seen = new Set()
  return courses.filter((course) => {
    if (!isMeaningfulCourse(course)) return false
    const key = `${String(course.title || '').trim()}::${String(course.goal || '').trim()}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function getCourseIcon(course) {
  const title = course?.title || '课'
  if (/人工智能|AI|机器学习/.test(title)) return 'AI'
  if (/数据|结构|算法/.test(title)) return 'DS'
  return title.slice(0, 1).toUpperCase()
}

function formatRecentTime(value) {
  if (!value) return '暂无学习记录'
  const time = new Date(value).getTime()
  if (!Number.isFinite(time)) return '暂无学习记录'
  const diffDays = Math.max(0, Math.floor((Date.now() - time) / 86400000))
  if (diffDays === 0) return '今天学习过'
  if (diffDays === 1) return '昨天学习过'
  return `${diffDays} 天前学习`
}

function calcProgress(path) {
  return getPathProgress(path).percent
}

function getCourseLearningTarget(course, path) {
  if (!course) return '/courses'
  if (!path?.stages?.length) return `/course/${course.id}/path`
  const { task } = getCurrentLearningTarget(path)
  if (!task?.id) return `/course/${course.id}/path`
  return `/course/${course.id}/learn/${encodeURIComponent(task.id)}`
}

export default function CourseEntryPage() {
  const navigate = useNavigate()
  const { courses, activeCourse, activateCourse, createCourse } = useAuth()
  const [creating, setCreating] = useState(false)
  const [enteringId, setEnteringId] = useState(null)
  const [loadingMeta, setLoadingMeta] = useState(true)
  const [courseMeta, setCourseMeta] = useState({})

  const visibleCourses = useMemo(() => normalizeCourses(courses), [courses])
  const currentCourse = useMemo(() => {
    if (activeCourse && isMeaningfulCourse(activeCourse)) return activeCourse
    return visibleCourses[0] || null
  }, [activeCourse, visibleCourses])
  const otherCourses = visibleCourses.filter((course) => course.id !== currentCourse?.id)

  useEffect(() => {
    let cancelled = false
    async function loadMeta() {
      setLoadingMeta(true)
      try {
        const entries = await Promise.all(
          visibleCourses.map(async (course) => {
            const path = await getLearningPath(course.student_id).catch(() => null)
            return [course.id, { path, progress: calcProgress(path) }]
          }),
        )
        if (!cancelled) setCourseMeta(Object.fromEntries(entries))
      } finally {
        if (!cancelled) setLoadingMeta(false)
      }
    }
    loadMeta()
    return () => { cancelled = true }
  }, [visibleCourses])

  const enterCourse = useCallback(async (course) => {
    if (!course) return
    setEnteringId(course.id)
    try {
      if (course.id !== activeCourse?.id) await activateCourse(course.id)
      navigate(getCourseLearningTarget(course, courseMeta[course.id]?.path))
    } catch (error) {
      message.error(error.message || '进入课程失败')
    } finally {
      setEnteringId(null)
    }
  }, [activateCourse, activeCourse, courseMeta, navigate])

  const handleCreate = useCallback(async () => {
    setCreating(true)
    try {
      const course = await createCourse(`新课程 ${visibleCourses.length + 1}`, '')
      message.success('已创建课程空间，请先和 ChatBox 完成课程画像')
      navigate(`/course/${course.id}/profile/setup`, { state: { newCourse: true } })
    } catch (error) {
      message.error(error.message || '创建课程失败')
    } finally {
      setCreating(false)
    }
  }, [createCourse, navigate, visibleCourses.length])

  return (
    <div className="courses-page">
      <div className="courses-container">
        <div className="courses-header">
          <div>
            <Title level={2}>我的课程</Title>
            <Text>管理你的课程空间、学习进度和下一步任务。</Text>
          </div>
        </div>

        {loadingMeta ? (
          <Skeleton active paragraph={{ rows: 8 }} />
        ) : visibleCourses.length === 0 ? (
          <Card className="courses-empty-card">
            <Empty description="暂无课程">
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate} loading={creating}>
                创建新课程
              </Button>
            </Empty>
          </Card>
        ) : (
          <>
            {currentCourse && (
              <Card className="current-course-card">
                <div className="current-course-layout">
                  <Avatar className="course-avatar current">{getCourseIcon(currentCourse)}</Avatar>
                  <div className="current-course-copy">
                    <Text className="current-label">当前课程</Text>
                    <Title level={3}>{currentCourse.title}</Title>
                    <Paragraph>{currentCourse.goal || '继续完善课程目标，系统会根据画像推荐学习路径。'}</Paragraph>
                    <Space size={18} wrap>
                      <Text><BookOutlined /> 当前章节：{courseMeta[currentCourse.id]?.path?.stages?.[0]?.title || '等待生成路径'}</Text>
                      <Text><ClockCircleOutlined /> {formatRecentTime(currentCourse.updated_at || currentCourse.updatedAt)}</Text>
                    </Space>
                  </div>
                  <div className="current-course-actions">
                    <Progress
                      type="circle"
                      percent={courseMeta[currentCourse.id]?.progress || 0}
                      strokeColor="#6C5CE7"
                      size={92}
                    />
                    <Button type="primary" icon={<ArrowRightOutlined />} loading={enteringId === currentCourse.id} onClick={() => enterCourse(currentCourse)}>
                      继续学习
                    </Button>
                    <Button icon={<ProfileOutlined />} onClick={() => navigate(`/course/${currentCourse.id}/path`)}>
                      查看路径
                    </Button>
                  </div>
                </div>
              </Card>
            )}

            <div className="course-grid">
              {otherCourses.map((course) => (
                <Card className="compact-course-card" key={course.id} hoverable>
                  <div className="compact-course-top">
                    <Avatar className="course-avatar">{getCourseIcon(course)}</Avatar>
                    <Button type="text" icon={<RightOutlined />} loading={enteringId === course.id} onClick={() => enterCourse(course)} />
                  </div>
                  <Title level={5}>{course.title}</Title>
                  <Paragraph>{course.goal || '尚未设置明确目标'}</Paragraph>
                  <Progress percent={courseMeta[course.id]?.progress || 0} showInfo={false} strokeColor="#20C7B7" />
                  <div className="compact-course-footer">
                    <Text>{formatRecentTime(course.updated_at || course.updatedAt)}</Text>
                    <Button type="link" onClick={() => enterCourse(course)}>进入课程</Button>
                  </div>
                </Card>
              ))}

              <Card className="create-course-card" hoverable onClick={handleCreate}>
                <PlusOutlined />
                <Text strong>创建新课程</Text>
                <Text type="secondary">通过 ChatBox 建立新的课程画像和路径</Text>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
