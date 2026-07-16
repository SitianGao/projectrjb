import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import {
  Typography, Card, Tag, Button, Modal, Space, Row, Col,
  Result, Empty, Progress, Statistic, Collapse, Divider, message, Spin,
} from 'antd'
import {
  ArrowLeftOutlined,
  BookOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  AimOutlined,
  TagsOutlined,
  UnorderedListOutlined,
  FileTextOutlined,
  EditOutlined,
  QuestionCircleOutlined,
  CodeOutlined,
  BranchesOutlined,
  ExpandOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  FlagFilled,
  ReloadOutlined,
  ThunderboltOutlined,
  PlayCircleFilled,
  LockFilled,
  CheckCircleFilled,
} from '@ant-design/icons'
import MarkdownRenderer from '../components/MarkdownRenderer'
import ResourceCard from '../components/ResourceCard'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { getLearningPath } from '../api/planner'
import { getResources, getResource, generateResources } from '../api/resource'
import { shouldUseMock } from '../utils/useMock'
import { matchResourcesToStage, computeStageDays, getStageStatus } from '../utils/stageUtils'

const USE_MOCK = shouldUseMock()
const { Title, Text, Paragraph } = Typography
const STUDENT_ID = 'demo-student-01'

const TYPE_CONFIG = {
  document: { icon: <FileTextOutlined />, color: 'blue', label: '文档' },
  exercise: { icon: <EditOutlined />, color: 'green', label: '练习' },
  quiz: { icon: <QuestionCircleOutlined />, color: 'orange', label: '测验' },
  code: { icon: <CodeOutlined />, color: 'red', label: '代码' },
  mindmap: { icon: <BranchesOutlined />, color: 'purple', label: '导图' },
}

const TASK_TYPE_ICONS = {
  study: '📖', exercise: '✏️', quiz: '📝', project: '🔨', review: '🔁',
}

const DIFFICULTY_COLORS = {
  '初级': 'green', '中级': 'blue', '高级': 'orange', '专家': 'red',
}

const STATUS_CONFIG = {
  completed: { icon: CheckCircleFilled, color: 'var(--stage-completed)', label: '已完成', tagColor: 'green' },
  in_progress: { icon: PlayCircleFilled, color: 'var(--stage-inprogress)', label: '进行中', tagColor: 'processing' },
  locked: { icon: LockFilled, color: 'var(--stage-locked-dot)', label: '未解锁', tagColor: 'default' },
}

export default function StageResourcePage() {
  const { stageId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  // 从导航状态获取 stage / pathId，刷新时丢失则从 API 恢复
  const navState = location.state || {}

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pathData, setPathData] = useState(null)
  const [stage, setStage] = useState(navState.stage || null)
  const [resources, setResources] = useState([])
  const [matchedResources, setMatchedResources] = useState([])
  const [generating, setGenerating] = useState(false)

  // 资源详情弹窗
  const [selectedResource, setSelectedResource] = useState(null)
  const [resourceModalVisible, setResourceModalVisible] = useState(false)
  const [resourceLoading, setResourceLoading] = useState(false)
  const [resourceError, setResourceError] = useState(null)

  // 首次加载
  useEffect(() => {
    loadData()
  }, [stageId])

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const path = await getLearningPath(STUDENT_ID)
      setPathData(path)

      // 找到对应阶段
      const found = path?.stages?.find(
        (s) => String(s.stage_id) === String(stageId),
      )
      if (!found) {
        setError(`未找到阶段 ${stageId}`)
        setLoading(false)
        return
      }
      setStage(found)

      // 加载资源
      const resList = await getResources({
        student_id: STUDENT_ID,
        page_size: 100,
      })
      const allResources = resList?.items || []
      setResources(allResources)
      setMatchedResources(matchResourcesToStage(found, allResources))
    } catch (err) {
      setError(err.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 生成资源
  const handleGenerateResources = useCallback(async () => {
    if (!stage) return
    setGenerating(true)
    try {
      const firstTopic = stage.topics?.[0] || stage.title
      message.loading({ content: '正在生成学习资源...', key: 'gen', duration: 0 })
      await generateResources({
        student_id: STUDENT_ID,
        topic: firstTopic,
        path_id: pathData?.id,
      })
      message.success({ content: '资源生成任务已创建，请稍后刷新查看', key: 'gen' })
      // 刷新资源
      setTimeout(() => loadData(), 2000)
    } catch (err) {
      message.error({ content: err.message || '生成失败', key: 'gen' })
    } finally {
      setGenerating(false)
    }
  }, [stage, pathData])

  // 点击资源
  const handleResourceClick = useCallback(async (resource) => {
    setResourceError(null)
    setSelectedResource(resource)
    setResourceModalVisible(true)

    if (resource.content) return

    setResourceLoading(true)
    try {
      const detail = await getResource(resource.id)
      if (detail) {
        setSelectedResource({ ...resource, ...detail })
      }
    } catch (err) {
      setResourceError(err.message || '加载资源详情失败')
    } finally {
      setResourceLoading(false)
    }
  }, [])

  const handleCloseModal = useCallback(() => {
    setResourceModalVisible(false)
    setSelectedResource(null)
    setResourceError(null)
  }, [])

  // ── 加载态 ──
  if (loading) {
    return (
      <div style={{ height: '100%', overflow: 'auto', background: 'var(--bg-page)' }}>
        <LoadingSkeleton type="detail" />
      </div>
    )
  }

  // ── 错误态 ──
  if (error) {
    return (
      <div style={{ maxWidth: 600, margin: '60px auto', padding: 24 }}>
        <Result
          status="error"
          title="加载失败"
          subTitle={error}
          extra={
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
                返回课程
              </Button>
              <Button type="primary" icon={<ReloadOutlined />} onClick={loadData}>
                重试
              </Button>
            </Space>
          }
        />
      </div>
    )
  }

  if (!stage) {
    return (
      <div style={{ maxWidth: 600, margin: '60px auto', padding: 24 }}>
        <Result
          status="404"
          title="阶段未找到"
          subTitle={`未找到阶段 ${stageId}，可能已被删除或链接无效`}
          extra={
            <Button type="primary" icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
              返回课程
            </Button>
          }
        />
      </div>
    )
  }

  const currentStage = pathData?.current_stage || 1
  const status = getStageStatus(stage, currentStage)
  const statusCfg = STATUS_CONFIG[status]
  const StatusIcon = statusCfg.icon
  const stageDays = computeStageDays(stage)
  const stageCompleted = stage.tasks?.filter((t) => t.status === 'completed')?.length || 0
  const stageTotal = stage.tasks?.length || 0

  return (
    <div style={{ height: '100%', overflow: 'auto', background: 'var(--bg-page)', padding: '20px 24px' }}>
      <div style={{ maxWidth: 1060, margin: '0 auto' }}>
        {/* 返回按钮 */}
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
          style={{ marginBottom: 16, paddingLeft: 0 }}
        >
          返回课程
        </Button>

        {/* 阶段头部卡片 */}
        <Card
          style={{
            borderRadius: 16,
            marginBottom: 24,
            borderLeft: `4px solid ${statusCfg.color}`,
          }}
          styles={{ body: { padding: '24px 28px' } }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
            <div style={{ flex: 1 }}>
              <Space size={8} style={{ marginBottom: 8 }}>
                <FlagFilled style={{ color: statusCfg.color }} />
                <Title level={3} style={{ margin: 0 }}>
                  第{stage.stage_id}阶段：{stage.title}
                </Title>
                <Tag icon={<StatusIcon />} color={statusCfg.tagColor}>{statusCfg.label}</Tag>
              </Space>
              {stage.description && (
                <Paragraph type="secondary" style={{ margin: '8px 0 0', fontSize: 14, lineHeight: 1.7 }}>
                  {stage.description}
                </Paragraph>
              )}
            </div>
            <Space size={32}>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>任务进度</Text>
                <Text strong style={{ fontSize: 20 }}>
                  {stageCompleted}/{stageTotal}
                </Text>
              </div>
              <div style={{ textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>匹配资源</Text>
                <Text strong style={{ fontSize: 20, color: 'var(--color-primary)' }}>
                  {matchedResources.length}
                </Text>
              </div>
              <Progress
                type="circle"
                percent={stageTotal > 0 ? Math.round((stageCompleted / stageTotal) * 100) : 0}
                size={56}
                strokeColor={{ '0%': 'var(--color-primary)', '100%': 'var(--color-success)' }}
              />
            </Space>
          </div>

          {/* 目标 & 主题标签 */}
          <div style={{ marginTop: 16 }}>
            <Space size={4} wrap>
              {stage.objectives?.map((obj, oi) => (
                <Tag key={`obj-${oi}`} icon={<AimOutlined />} color="blue" style={{ fontSize: 12 }}>
                  {obj}
                </Tag>
              ))}
              {stage.topics?.map((topic) => (
                <Tag key={topic} icon={<TagsOutlined />} color="purple" style={{ fontSize: 12 }}>
                  {topic}
                </Tag>
              ))}
            </Space>
          </div>

          {/* 统计行 */}
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={12} sm={6}>
              <Statistic
                title="学习任务"
                value={stageTotal}
                suffix="项"
                prefix={<UnorderedListOutlined style={{ color: 'var(--color-primary)' }} />}
                valueStyle={{ fontSize: 20 }}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic
                title="预计天数"
                value={stageDays}
                suffix="天"
                prefix={<ClockCircleOutlined style={{ color: 'var(--color-warning)' }} />}
                valueStyle={{ fontSize: 20 }}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic
                title="已完成"
                value={stageCompleted}
                suffix={`/ ${stageTotal}`}
                prefix={<TrophyOutlined style={{ color: 'var(--color-success)' }} />}
                valueStyle={{ fontSize: 20 }}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic
                title="匹配资源"
                value={matchedResources.length}
                suffix="个"
                prefix={<BookOutlined style={{ color: 'var(--color-purple)' }} />}
                valueStyle={{ fontSize: 20 }}
              />
            </Col>
          </Row>
        </Card>

        {/* 任务列表 */}
        {stage.tasks?.length > 0 && (
          <Card
            title={
              <Space>
                <UnorderedListOutlined />
                <Text strong>学习任务（{stage.tasks.length} 项）</Text>
              </Space>
            }
            style={{ borderRadius: 12, marginBottom: 24 }}
            styles={{ body: { padding: '12px 20px 20px' } }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {stage.tasks.map((task) => {
                const diffColor = DIFFICULTY_COLORS[task.difficulty] || 'default'
                const isCompleted = task.status === 'completed'
                return (
                  <div
                    key={task.task_id}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '8px 14px', borderRadius: 8,
                      background: isCompleted ? 'var(--stage-completed-bg)' : 'var(--surface-secondary)',
                      border: `1px solid ${isCompleted ? 'var(--stage-completed-border)' : 'var(--border)'}`,
                      opacity: isCompleted ? 0.85 : 1,
                    }}
                  >
                    <span style={{ fontSize: 16 }}>{TASK_TYPE_ICONS[task.type] || '📌'}</span>
                    <span style={{
                      flex: 1, fontSize: 14,
                      textDecoration: isCompleted ? 'line-through' : 'none',
                      color: isCompleted ? 'var(--color-text-disabled)' : 'var(--text-primary)',
                    }}>
                      {task.description}
                    </span>
                    <Tag color={diffColor} style={{ fontSize: 11 }}>{task.difficulty}</Tag>
                    {task.estimated_hours != null && (
                      <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
                        ⏱ {task.estimated_hours}h
                      </Text>
                    )}
                    {isCompleted && <CheckCircleFilled style={{ color: 'var(--color-success)', fontSize: 14 }} />}
                  </div>
                )
              })}
            </div>
            {stageTotal > 0 && (
              <Progress
                percent={Math.round((stageCompleted / stageTotal) * 100)}
                style={{ marginTop: 12 }}
                strokeColor={stageCompleted === stageTotal ? 'var(--color-success)' : 'var(--color-primary)'}
              />
            )}
          </Card>
        )}

        {/* 匹配资源 */}
        <Card
          title={
            <Space>
              <BookOutlined />
              <Text strong>匹配资源（{matchedResources.length} 个）</Text>
            </Space>
          }
          extra={
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={handleGenerateResources}
              loading={generating}
              size="small"
            >
              生成学习资源
            </Button>
          }
          style={{ borderRadius: 12, marginBottom: 24 }}
          styles={{ body: { padding: '16px 20px 20px' } }}
        >
          {matchedResources.length === 0 ? (
            <Empty description="该阶段暂无匹配的学习资源">
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={handleGenerateResources}
                loading={generating}
              >
                AI 生成学习资源
              </Button>
            </Empty>
          ) : (
            <Row gutter={[16, 16]}>
              {matchedResources.map((res) => (
                <Col xs={24} sm={12} md={8} key={res.id}>
                  <ResourceCard
                    resource={res}
                    onClick={handleResourceClick}
                  />
                </Col>
              ))}
            </Row>
          )}
        </Card>

        {/* 资源详情弹窗 */}
        <Modal
          title={
            selectedResource ? (
              <Space>
                {(() => { const cfg = TYPE_CONFIG[selectedResource.type] || TYPE_CONFIG.document; return <Tag icon={cfg.icon} color={cfg.color}>{cfg.label}</Tag> })()}
                <Text strong style={{ fontSize: 16 }}>{selectedResource.title}</Text>
              </Space>
            ) : ''
          }
          open={resourceModalVisible}
          onCancel={handleCloseModal}
          footer={
            <Button onClick={handleCloseModal}>关闭</Button>
          }
          width={720}
          style={{ top: 40 }}
          styles={{ body: { maxHeight: '70vh', overflow: 'auto', padding: '20px 28px' } }}
        >
          {resourceError ? (
            <Result
              status="error"
              title="无法加载资源内容"
              subTitle={resourceError}
              extra={
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={() => selectedResource && handleResourceClick(selectedResource)}
                >
                  重试
                </Button>
              }
            />
          ) : resourceLoading ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Spin tip="加载资源内容..." />
            </div>
          ) : selectedResource ? (
            <>
              <Space wrap style={{ marginBottom: 16 }}>
                {selectedResource.topic && <Tag color="purple">{selectedResource.topic}</Tag>}
                {selectedResource.difficulty && (
                  <Tag color={DIFFICULTY_COLORS[selectedResource.difficulty] || 'default'}>
                    {selectedResource.difficulty}
                  </Tag>
                )}
              </Space>
              {selectedResource.content ? (
                <MarkdownRenderer content={selectedResource.content} />
              ) : (
                <Empty description="暂无内容" />
              )}
            </>
          ) : null}
        </Modal>
      </div>
    </div>
  )
}
