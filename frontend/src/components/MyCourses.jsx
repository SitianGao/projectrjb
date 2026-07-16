import { useState, useEffect } from 'react'
import { Card, Row, Col, Tag, Space, Typography, Button, Empty, Spin, Progress, Tooltip, Modal, message } from 'antd'
import {
  BookOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  RocketOutlined,
  RightOutlined,
  FireOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  PauseCircleOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import { getAllLearningPaths, deleteLearningPath } from '../api/planner'
import { useNavigate } from 'react-router-dom'

const { Text, Paragraph } = Typography

// 状态颜色映射
const STATUS_CONFIG = {
  active: { color: 'green', icon: <SyncOutlined spin />, label: '进行中' },
  completed: { color: 'blue', icon: <CheckCircleOutlined />, label: '已完成' },
  paused: { color: 'orange', icon: <PauseCircleOutlined />, label: '已暂停' },
  superseded: { color: 'default', icon: <BookOutlined />, label: '历史版本' },
}

// 课程主题颜色（根据 goal 内容分配）
const TOPIC_COLORS = [
  '#8b5cf6', // 紫色
  '#3b82f6', // 蓝色
  '#10b981', // 绿色
  '#f59e0b', // 橙色
  '#ef4444', // 红色
  '#06b6d4', // 青色
  '#ec4899', // 粉色
  '#6366f1', // 靛蓝
]

function getTopicColor(index) {
  return TOPIC_COLORS[index % TOPIC_COLORS.length]
}

// 从 goal 中提取课程主题
function extractTopic(goal) {
  if (!goal) return '学习课程'
  // 移除常见前缀
  const cleaned = goal
    .replace(/^(学习|掌握|精通|提升|提高|加强|巩固)/, '')
    .replace(/^(数学|语文|英语|物理|化学|生物|历史|地理|政治)/, '$1')
    .trim()
  return cleaned.length > 20 ? cleaned.substring(0, 20) + '...' : cleaned
}

// 计算路径进度
function calculateProgress(path) {
  const stages = path.stages || []
  if (stages.length === 0) return 0

  const totalTasks = stages.reduce((sum, stage) => sum + (stage.tasks?.length || 0), 0)
  if (totalTasks === 0) return 0

  const completedTasks = stages.reduce(
    (sum, stage) => sum + (stage.tasks?.filter(t => t.status === 'completed')?.length || 0),
    0
  )

  return Math.round((completedTasks / totalTasks) * 100)
}

// 计算总学习天数
function calculateTotalDays(path) {
  const stages = path.stages || []
  return stages.reduce((sum, stage) => sum + (stage.estimated_days || 0), 0)
}

export default function MyCourses({ studentId = 'demo-student-01' }) {
  const [paths, setPaths] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadPaths()
  }, [studentId])

  async function loadPaths() {
    setLoading(true)
    setError(null)
    try {
      const data = await getAllLearningPaths(studentId)
      setPaths(Array.isArray(data) ? data : [])
    } catch (err) {
      setError('加载课程失败')
      console.error('Failed to load paths:', err)
    } finally {
      setLoading(false)
    }
  }

  function handleDelete(pathId, goal) {
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除课程"${goal || '未命名课程'}"吗？此操作不可撤销。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        setDeleting(pathId)
        try {
          await deleteLearningPath(studentId, pathId)
          message.success('删除成功')
          setPaths(prev => prev.filter(p => p.id !== pathId))
        } catch (err) {
          message.error('删除失败')
          console.error('Failed to delete path:', err)
        } finally {
          setDeleting(null)
        }
      },
    })
  }

  if (loading) {
    return (
      <div>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 8 }}>
            <div style={{ width: 40, height: 2, background: 'linear-gradient(90deg, transparent, #8b5cf6)', borderRadius: 1 }} />
            <BookOutlined style={{ color: '#8b5cf6', fontSize: 24 }} />
            <Text strong style={{ fontSize: 22, color: 'var(--text-primary)', letterSpacing: 2 }}>
              我的课程
            </Text>
            <BookOutlined style={{ color: '#8b5cf6', fontSize: 24 }} />
            <div style={{ width: 40, height: 2, background: 'linear-gradient(90deg, #8b5cf6, transparent)', borderRadius: 1 }} />
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16, color: 'var(--text-muted)', fontSize: 14 }}>加载课程中...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 8 }}>
            <div style={{ width: 40, height: 2, background: 'linear-gradient(90deg, transparent, #8b5cf6)', borderRadius: 1 }} />
            <BookOutlined style={{ color: '#8b5cf6', fontSize: 24 }} />
            <Text strong style={{ fontSize: 22, color: 'var(--text-primary)', letterSpacing: 2 }}>
              我的课程
            </Text>
            <BookOutlined style={{ color: '#8b5cf6', fontSize: 24 }} />
            <div style={{ width: 40, height: 2, background: 'linear-gradient(90deg, #8b5cf6, transparent)', borderRadius: 1 }} />
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ color: '#ff4d4f', marginBottom: 16, fontSize: 14 }}>{error}</div>
          <Button icon={<SyncOutlined />} onClick={loadPaths} style={{ borderRadius: 20 }}>重试</Button>
        </div>
      </div>
    )
  }

  if (paths.length === 0) {
    return (
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 8 }}>
          <div style={{ width: 40, height: 2, background: 'linear-gradient(90deg, transparent, #8b5cf6)', borderRadius: 1 }} />
          <BookOutlined style={{ color: '#8b5cf6', fontSize: 24 }} />
          <Text strong style={{ fontSize: 22, color: 'var(--text-primary)', letterSpacing: 2 }}>
            我的课程
          </Text>
          <BookOutlined style={{ color: '#8b5cf6', fontSize: 24 }} />
          <div style={{ width: 40, height: 2, background: 'linear-gradient(90deg, #8b5cf6, transparent)', borderRadius: 1 }} />
        </div>
      <Card
        style={{
          borderRadius: 16,
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          marginTop: 16,
        }}
      >
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div>
              <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: 'var(--text-primary)' }}>还没有学习课程</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 14, lineHeight: '1.6' }}>
                和 AI 助手聊聊你的学习情况，为你定制专属学习路径
              </div>
            </div>
          }
        >
          <Button
            type="primary"
            icon={<RocketOutlined />}
            size="large"
            style={{ borderRadius: 20, padding: '0 28px' }}
            onClick={() => navigate('/profile', { state: { startChat: true } })}
          >
            开始对话
          </Button>
        </Empty>
      </Card>
      </div>
    )
  }

  // 按状态分组：active 在前，然后是其他状态
  const sortedPaths = [...paths].sort((a, b) => {
    if (a.status === 'active' && b.status !== 'active') return -1
    if (a.status !== 'active' && b.status === 'active') return 1
    return new Date(b.created_at) - new Date(a.created_at)
  })

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 8 }}>
          <div style={{ width: 40, height: 2, background: 'linear-gradient(90deg, transparent, #8b5cf6)', borderRadius: 1 }} />
          <BookOutlined style={{ color: '#8b5cf6', fontSize: 24 }} />
          <Text strong style={{ fontSize: 22, color: 'var(--text-primary)', letterSpacing: 2 }}>
            我的课程
          </Text>
          <BookOutlined style={{ color: '#8b5cf6', fontSize: 24 }} />
          <div style={{ width: 40, height: 2, background: 'linear-gradient(90deg, #8b5cf6, transparent)', borderRadius: 1 }} />
        </div>
        <Tag color="purple" style={{ fontSize: 13, padding: '2px 12px' }}>{paths.length} 个课程</Tag>
        <div style={{ marginTop: 8 }}>
          <Button size="small" icon={<SyncOutlined />} onClick={loadPaths}>刷新</Button>
        </div>
      </div>

      <Row gutter={[20, 20]}>
        {sortedPaths.map((path, index) => {
          const progress = calculateProgress(path)
          const totalDays = calculateTotalDays(path)
          const topic = extractTopic(path.goal)
          const statusConfig = STATUS_CONFIG[path.status] || STATUS_CONFIG.active
          const color = getTopicColor(index)

          return (
            <Col xs={24} sm={12} lg={8} key={path.id}>
              <Card
                hoverable
                style={{
                  borderRadius: 16,
                  background: 'var(--bg-card)',
                  border: path.status === 'active'
                    ? `2px solid ${color}`
                    : '1px solid var(--border)',
                  transition: 'all 0.3s',
                  height: '100%',
                  boxShadow: path.status === 'active'
                    ? `0 4px 16px ${color}20`
                    : '0 2px 8px rgba(0,0,0,0.04)',
                  overflow: 'hidden',
                }}
                styles={{
                  body: { padding: '20px' },
                }}
                onClick={() => {
                  if (path.status === 'active') {
                    navigate(`/journey?pathId=${path.id}`)
                  }
                }}
              >
                {/* 顶部：主题标签 + 状态 */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        display: 'inline-block',
                        padding: '6px 16px',
                        borderRadius: 24,
                        background: `linear-gradient(135deg, ${color}15, ${color}25)`,
                        color: color,
                        fontWeight: 600,
                        fontSize: 15,
                        marginBottom: 10,
                        border: `1px solid ${color}30`,
                      }}
                    >
                      {topic}
                    </div>
                    <div>
                      <Tag
                        icon={statusConfig.icon}
                        color={statusConfig.color}
                        style={{ margin: 0, borderRadius: 12, padding: '2px 10px' }}
                      >
                        {statusConfig.label}
                      </Tag>
                    </div>
                  </div>
                  <Space size={8}>
                    <Tooltip title="删除课程">
                      <Button
                        type="text"
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                        loading={deleting === path.id}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(path.id, path.goal)
                        }}
                        style={{
                          width: 32,
                          height: 32,
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      />
                    </Tooltip>
                    {path.status === 'active' && (
                      <div style={{
                        width: 32,
                        height: 32,
                        borderRadius: '50%',
                        background: `${color}15`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}>
                        <RightOutlined style={{ color, fontSize: 14 }} />
                      </div>
                    )}
                  </Space>
                </div>

                {/* 学习目标 */}
                {path.goal && (
                  <Paragraph
                    ellipsis={{ rows: 2 }}
                    style={{
                      color: 'var(--text-secondary)',
                      fontSize: 13,
                      marginBottom: 16,
                      minHeight: 40,
                      lineHeight: '1.6',
                    }}
                  >
                    🎯 {path.goal}
                  </Paragraph>
                )}

                {/* 进度条 */}
                <div style={{ marginBottom: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>学习进度</Text>
                    <Text strong style={{ fontSize: 14, color }}>{progress}%</Text>
                  </div>
                  <Progress
                    percent={progress}
                    showInfo={false}
                    strokeColor={{
                      '0%': color,
                      '100%': `${color}99`,
                    }}
                    trailColor="var(--bg-page)"
                    size={['100%', 8]}
                    style={{ marginBottom: 0 }}
                  />
                </div>

                {/* 统计信息 */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-around',
                  padding: '12px 0',
                  background: 'var(--bg-page)',
                  borderRadius: 10,
                  marginBottom: 12,
                }}>
                  <Tooltip title="学习阶段数">
                    <div style={{ textAlign: 'center' }}>
                      <BookOutlined style={{ color: '#1677ff', fontSize: 18 }} />
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                        {path.stages?.length || 0} 阶段
                      </div>
                    </div>
                  </Tooltip>
                  <Tooltip title="预计学习天数">
                    <div style={{ textAlign: 'center' }}>
                      <ClockCircleOutlined style={{ color: '#fa8c16', fontSize: 18 }} />
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                        {totalDays} 天
                      </div>
                    </div>
                  </Tooltip>
                  <Tooltip title="当前阶段">
                    <div style={{ textAlign: 'center' }}>
                      <FireOutlined style={{ color: '#eb2f96', fontSize: 18 }} />
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                        第 {path.current_stage || 1} 阶段
                      </div>
                    </div>
                  </Tooltip>
                </div>

                {/* 创建时间 */}
                <div style={{ textAlign: 'right' }}>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {path.created_at ? new Date(path.created_at).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }) : ''}
                  </Text>
                </div>
              </Card>
            </Col>
          )
        })}
      </Row>
    </div>
  )
}