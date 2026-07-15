import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Typography, Card, Button, Space, Row, Col, Result, message } from 'antd'
import {
  FileTextOutlined,
  BranchesOutlined,
  EditOutlined,
  ReadOutlined,
  CodeOutlined,
  CheckCircleFilled,
  LoadingOutlined,
  ReloadOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { generateResources, getTaskStatus } from '../api/resource'
import { useTaskStatus } from '../hooks/useTaskStatus'

const { Title, Text } = Typography

// ==================== 资源类型定义 ====================

const RESOURCE_TYPES = [
  { key: 'document', name: '专业课程讲解文档', icon: <FileTextOutlined />, color: '#1677ff' },
  { key: 'mindmap',  name: '知识点思维导图',   icon: <BranchesOutlined />,  color: '#8b5cf6' },
  { key: 'exercise', name: '不同类型练习题目', icon: <EditOutlined />,       color: '#52c41a' },
  { key: 'reading',  name: '拓展阅读材料',     icon: <ReadOutlined />,       color: '#fa8c16' },
  { key: 'code',     name: '代码类实操案例',   icon: <CodeOutlined />,       color: '#eb2f96' },
]

const SEGMENT_SIZE = 100 / RESOURCE_TYPES.length // 每类资源 20%

// ==================== 工具函数 ====================

function getResourceProgress(overallPercent, index) {
  const segmentStart = index * SEGMENT_SIZE
  if (overallPercent <= segmentStart) return 0
  if (overallPercent >= segmentStart + SEGMENT_SIZE) return 100
  return ((overallPercent - segmentStart) / SEGMENT_SIZE) * 100
}

// ==================== 主组件 ====================

export default function ResourceGenerationPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { studentId, pathId, topic } = location.state || {}

  const redirectedRef = useRef(false)
  const initiatedRef = useRef(false)

  const [generateError, setGenerateError] = useState(null)
  const [generating, setGenerating] = useState(false)

  // 包装 getTaskStatus：后端返回 'done'，useTaskStatus 期望 'completed'
  const fetchTaskStatus = useCallback(async (taskId) => {
    const raw = await getTaskStatus(taskId)
    return {
      ...raw,
      status: raw.status === 'done' ? 'completed' : raw.status,
    }
  }, [])

  const {
    status: taskStatus,
    error: pollError,
    progress,
    taskMessage,
    startPolling,
    reset: resetPolling,
  } = useTaskStatus(fetchTaskStatus, { interval: 2000 })

  // ── 注入 shimmer 动画 ──
  useEffect(() => {
    const id = 'rg-shimmer'
    if (document.getElementById(id)) return
    const style = document.createElement('style')
    style.id = id
    style.textContent = [
      '@keyframes rg-shimmer {',
      '  0%   { left: -100%; }',
      '  100% { left: 100%; }',
      '}',
    ].join('\n')
    document.head.appendChild(style)
  }, [])

  // ── 无导航 state：直接 URL 访问或刷新 → 重定向回首页 ──
  useEffect(() => {
    if (redirectedRef.current) return
    if (!studentId || !pathId || !topic) {
      redirectedRef.current = true
      message.warning('缺少生成参数，请返回首页重新开始')
      navigate('/', { replace: true })
    }
  }, [studentId, pathId, topic, navigate])

  // ── 发起资源生成 ──
  useEffect(() => {
    if (!studentId || !pathId || !topic) return
    if (initiatedRef.current) return
    initiatedRef.current = true

    async function initiate() {
      setGenerating(true)
      setGenerateError(null)
      try {
        const result = await generateResources({
          student_id: studentId,
          topic,
          path_id: pathId,
          types: RESOURCE_TYPES.map((r) => r.key),
        })
        const taskId = result?.task_id
        if (!taskId) {
          throw new Error('资源生成任务创建失败')
        }
        startPolling(taskId)
      } catch (err) {
        setGenerateError(err.message || '资源生成请求失败')
      } finally {
        setGenerating(false)
      }
    }

    initiate()
  }, [studentId, pathId, topic, startPolling])

  // ── 任务完成后自动跳转到学习旅程 ──
  useEffect(() => {
    if (taskStatus === 'completed') {
      const timer = setTimeout(() => {
        navigate('/journey', { replace: true })
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [taskStatus, navigate])

  // ── 无导航 state，显示 loading ──
  if (!studentId || !pathId || !topic) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-page)' }}>
        <LoadingSkeleton type="detail" />
      </div>
    )
  }

  // ── generateResources API 调用失败 ──
  if (generateError) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-page)' }}>
        <Result
          status="error"
          title="资源生成启动失败"
          subTitle={generateError}
          extra={
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => {
                setGenerateError(null)
                initiatedRef.current = false
                resetPolling()
              }}>重试</Button>
              <Button type="primary" icon={<RocketOutlined />} onClick={() => navigate('/', { replace: true })}>返回首页</Button>
            </Space>
          }
        />
      </div>
    )
  }

  // ── 任务执行失败 ──
  if (taskStatus === 'failed' || pollError) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-page)' }}>
        <Result
          status="error"
          title="资源生成失败"
          subTitle={pollError || '任务执行过程中出现错误'}
          extra={
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => {
                setGenerateError(null)
                if (pollError) resetPolling()
                initiatedRef.current = false
              }}>重试</Button>
              <Button icon={<RocketOutlined />} onClick={() => navigate('/', { replace: true })}>返回首页</Button>
            </Space>
          }
        />
      </div>
    )
  }

  // ── 初始加载中 ──
  if (generating || taskStatus === 'idle' || taskStatus === 'pending') {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-page)' }}>
        <LoadingSkeleton type="detail" />
      </div>
    )
  }

  // ── 主进度 UI ──
  const overallPercent = taskStatus === 'completed' ? 100 : Math.max(progress, 0)

  return (
    <div style={{ height: '100%', overflow: 'auto', background: 'var(--bg-page)' }}>
      <div style={{ maxWidth: 720, margin: '0 auto', padding: '48px 24px' }}>
        {/* 标题 */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <Title level={3} style={{ margin: 0, fontWeight: 700 }}>
            {taskStatus === 'completed' ? '🎉 学习资源已就绪！' : '正在为你生成学习资源...'}
          </Title>
          {topic && (
            <Text type="secondary" style={{ fontSize: 14, marginTop: 8, display: 'block' }}>
              学习主题：{topic}
            </Text>
          )}
          {taskMessage && taskStatus !== 'completed' && (
            <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
              {taskMessage}
            </Text>
          )}
        </div>

        {/* 总进度 */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{
            fontSize: 48, fontWeight: 800, lineHeight: 1.1,
            color: taskStatus === 'completed' ? '#22c55e' : '#7c3aed',
            transition: 'color 0.4s',
          }}>
            {taskStatus === 'completed' ? (
              <CheckCircleFilled style={{ fontSize: 42 }} />
            ) : (
              <span>
                {Math.round(overallPercent)}
                <span style={{ fontSize: 24, fontWeight: 500 }}>%</span>
              </span>
            )}
          </div>
          {taskStatus !== 'completed' && (
            <Text type="secondary" style={{ fontSize: 13, marginTop: 4, display: 'block' }}>
              AI 正在生成 5 类学习资源
            </Text>
          )}
        </div>

        {/* 5 类资源卡片 */}
        <Row gutter={[12, 12]}>
          {RESOURCE_TYPES.map((type, i) => {
            const resourceProgress = getResourceProgress(overallPercent, i)
            const isComplete = resourceProgress >= 100
            const isActive = resourceProgress > 0 && resourceProgress < 100

            return (
              <Col xs={24} sm={12} key={type.key}>
                <Card
                  style={{
                    borderRadius: 12,
                    border: isActive
                      ? `1px solid ${type.color}33`
                      : isComplete
                        ? '1px solid rgba(82,196,26,0.3)'
                        : '1px solid var(--border)',
                    background: 'var(--bg-card)',
                    transition: 'border-color 0.4s',
                  }}
                  styles={{ body: { padding: '20px 24px' } }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    {/* 图标 */}
                    <div style={{
                      width: 44, height: 44, borderRadius: '50%',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 20, flexShrink: 0,
                      background: isComplete
                        ? 'linear-gradient(135deg, #dcfce7, #f0fdf4)'
                        : isActive
                          ? `linear-gradient(135deg, ${type.color}18, ${type.color}08)`
                          : 'var(--surface-secondary)',
                      border: `2px solid ${isComplete ? '#22c55e' : isActive ? type.color : 'var(--border)'}`,
                      color: isComplete ? '#22c55e' : type.color,
                    }}>
                      {isComplete ? <CheckCircleFilled /> : type.icon}
                    </div>

                    {/* 名称 + 进度条 */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        fontSize: 14, fontWeight: 600,
                        color: isComplete ? '#22c55e' : 'var(--text-primary)',
                        marginBottom: 8,
                        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                      }}>
                        {type.name}
                      </div>

                      <div style={{ height: 6, borderRadius: 3, background: 'var(--progress-track)', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%', borderRadius: 3,
                          width: `${Math.max(resourceProgress, 0)}%`,
                          background: isComplete
                            ? 'linear-gradient(90deg, #22c55e, #4ade80)'
                            : `linear-gradient(90deg, ${type.color}, ${type.color}cc)`,
                          transition: 'width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
                          position: 'relative',
                          overflow: 'hidden',
                        }}>
                          {isActive && (
                            <span style={{
                              position: 'absolute', top: 0, bottom: 0, width: '60%',
                              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
                              animation: 'rg-shimmer 1.6s ease-in-out infinite',
                            }} />
                          )}
                        </div>
                      </div>

                      <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
                        {isActive && <LoadingOutlined style={{ marginRight: 4 }} spin />}
                        {isComplete ? '已完成' : isActive ? '生成中...' : '等待中'}
                      </div>
                    </div>
                  </div>
                </Card>
              </Col>
            )
          })}
        </Row>

        {/* 完成提示 */}
        {taskStatus === 'completed' && (
          <div style={{ textAlign: 'center', marginTop: 28 }}>
            <Text type="secondary">即将跳转到学习旅程...</Text>
          </div>
        )}
      </div>
    </div>
  )
}
