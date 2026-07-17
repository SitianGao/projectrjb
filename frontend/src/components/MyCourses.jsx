import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BookOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  FireOutlined,
  PlusOutlined,
  RightOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { Button, Card, Col, Empty, Progress, Row, Space, Spin, Tag, Tooltip, Typography, message } from 'antd'
import { getLearningPath } from '../api/planner'
import { useAuth } from '../contexts/AuthContext'

const { Text, Paragraph } = Typography

const TOPIC_COLORS = [
  '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b',
  '#ef4444', '#06b6d4', '#ec4899', '#6366f1',
]

function calculateProgress(path) {
  const stages = path?.stages || []
  const tasks = stages.flatMap((stage) => stage.tasks || [])
  if (!tasks.length) return 0
  return Math.round((tasks.filter((task) => task.status === 'completed').length / tasks.length) * 100)
}

function calculateTotalDays(path) {
  return (path?.stages || []).reduce(
    (sum, stage) => sum + Number(stage.estimated_days || 0),
    0,
  )
}

function SectionTitle({ count, onRefresh }) {
  return (
    <div style={{ textAlign: 'center', marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 8 }}>
        <div style={{ width: 40, height: 2, background: 'linear-gradient(90deg, transparent, #8b5cf6)' }} />
        <BookOutlined style={{ color: '#8b5cf6', fontSize: 24 }} />
        <Text strong style={{ fontSize: 22, color: 'var(--text-primary)', letterSpacing: 2 }}>
          我的课程
        </Text>
        <BookOutlined style={{ color: '#8b5cf6', fontSize: 24 }} />
        <div style={{ width: 40, height: 2, background: 'linear-gradient(90deg, #8b5cf6, transparent)' }} />
      </div>
      <Space>
        <Tag color="purple" style={{ fontSize: 13, padding: '2px 12px' }}>{count} 个课程</Tag>
        {onRefresh && <Button size="small" icon={<SyncOutlined />} onClick={onRefresh}>刷新</Button>}
      </Space>
    </div>
  )
}

/**
 * 保留队员 A 的卡片式 My Courses 交互，但数据源改为账号真实 courses。
 * 每门课程拥有独立 student_id，进入前必须先激活课程，杜绝跨课程串数据。
 */
export default function MyCourses() {
  const navigate = useNavigate()
  const {
    courses,
    activeCourse,
    activateCourse,
    createCourse,
  } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [enteringId, setEnteringId] = useState(null)
  const [creating, setCreating] = useState(false)

  const loadCourses = useCallback(async () => {
    setLoading(true)
    try {
      const resolved = await Promise.all(
        courses.map(async (course) => {
          try {
            const path = await getLearningPath(course.student_id)
            return { course, path }
          } catch {
            return { course, path: null }
          }
        }),
      )
      setItems(resolved)
    } finally {
      setLoading(false)
    }
  }, [courses])

  useEffect(() => {
    const timer = setTimeout(loadCourses, 0)
    return () => clearTimeout(timer)
  }, [loadCourses])

  const enterCourse = useCallback(async ({ course, path }) => {
    setEnteringId(course.id)
    try {
      if (course.id !== activeCourse?.id) {
        await activateCourse(course.id)
      }
      if (path?.id) {
        navigate(`/journey?pathId=${encodeURIComponent(path.id)}`)
      } else {
        navigate('/profile', { state: { startChat: true } })
      }
    } catch (error) {
      message.error(error.message || '进入课程失败')
    } finally {
      setEnteringId(null)
    }
  }, [activateCourse, activeCourse, navigate])

  const startNewCourse = useCallback(async () => {
    setCreating(true)
    try {
      await createCourse('待命名课程', '')
      navigate('/profile', { state: { startChat: true, newCourse: true } })
    } catch (error) {
      message.error(error.message || '新建课程失败')
    } finally {
      setCreating(false)
    }
  }, [createCourse, navigate])

  if (loading) {
    return (
      <div>
        <SectionTitle count={courses.length} />
        <div style={{ textAlign: 'center', padding: 48 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16, color: 'var(--text-muted)' }}>加载课程中...</div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <SectionTitle count={items.length} onRefresh={loadCourses} />

      {!items.length ? (
        <Card style={{ borderRadius: 16, border: '1px solid var(--border)' }}>
          <Empty description="还没有课程">
            <Button type="primary" icon={<PlusOutlined />} loading={creating} onClick={startNewCourse}>
              新建课程并开始对话
            </Button>
          </Empty>
        </Card>
      ) : (
        <Row gutter={[20, 20]}>
          {items.map(({ course, path }, index) => {
            const color = TOPIC_COLORS[index % TOPIC_COLORS.length]
            const progress = calculateProgress(path)
            const totalDays = calculateTotalDays(path)
            const isActive = course.id === activeCourse?.id
            const goal = path?.goal || course.goal || '请先通过 ChatBox 完善学习目标'
            return (
              <Col xs={24} sm={12} lg={8} key={course.id}>
                <Card
                  hoverable
                  loading={enteringId === course.id}
                  onClick={() => enterCourse({ course, path })}
                  style={{
                    height: '100%',
                    borderRadius: 16,
                    border: isActive ? `2px solid ${color}` : '1px solid var(--border)',
                    background: 'var(--bg-card)',
                    boxShadow: isActive ? `0 4px 16px ${color}20` : '0 2px 8px rgba(0,0,0,0.04)',
                  }}
                  styles={{ body: { padding: 20 } }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 14 }}>
                    <div>
                      <div style={{
                        display: 'inline-block',
                        padding: '6px 16px',
                        borderRadius: 24,
                        background: `${color}18`,
                        color,
                        fontWeight: 600,
                        marginBottom: 8,
                      }}>
                        {course.title}
                      </div>
                      <div>
                        <Tag
                          icon={path ? <CheckCircleOutlined /> : <ClockCircleOutlined />}
                          color={path ? (isActive ? 'green' : 'blue') : 'orange'}
                        >
                          {path ? (isActive ? '当前课程' : '可继续学习') : '待完成画像'}
                        </Tag>
                      </div>
                    </div>
                    <RightOutlined style={{ color, marginTop: 10 }} />
                  </div>

                  <Paragraph ellipsis={{ rows: 2 }} style={{ minHeight: 42, color: 'var(--text-secondary)' }}>
                    🎯 {goal}
                  </Paragraph>

                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>学习进度</Text>
                    <Text strong style={{ color }}>{progress}%</Text>
                  </div>
                  <Progress percent={progress} showInfo={false} strokeColor={color} />

                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-around',
                    padding: '12px 0',
                    background: 'var(--bg-page)',
                    borderRadius: 10,
                    marginTop: 12,
                  }}>
                    <Tooltip title="学习阶段数">
                      <Text><BookOutlined style={{ color: '#1677ff' }} /> {path?.stages?.length || 0} 阶段</Text>
                    </Tooltip>
                    <Tooltip title="预计学习天数">
                      <Text><ClockCircleOutlined style={{ color: '#fa8c16' }} /> {totalDays} 天</Text>
                    </Tooltip>
                    <Tooltip title="当前阶段">
                      <Text><FireOutlined style={{ color: '#eb2f96' }} /> 第 {path?.current_stage || 1} 阶段</Text>
                    </Tooltip>
                  </div>
                </Card>
              </Col>
            )
          })}
        </Row>
      )}

      <div style={{ textAlign: 'center', marginTop: 24 }}>
        <Button type="primary" icon={<PlusOutlined />} loading={creating} onClick={startNewCourse}>
          新建课程
        </Button>
      </div>
    </div>
  )
}
