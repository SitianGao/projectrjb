import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Typography, Card, Tag, Progress, Button, Modal, Space, Row, Col,
  Statistic, Result, Empty, Tooltip, Badge, Collapse, List, Divider, message,
} from 'antd'
import {
  CheckCircleFilled,
  PlayCircleFilled,
  LockFilled,
  ClockCircleOutlined,
  BookOutlined,
  ReloadOutlined,
  ExpandOutlined,
  FileTextOutlined,
  QuestionCircleOutlined,
  BranchesOutlined,
  CodeOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  FlagFilled,
  AimOutlined,
  TagsOutlined,
  UnorderedListOutlined,
  CaretRightOutlined,
  WarningFilled,
  CheckCircleOutlined,
  InboxOutlined,
  LeftOutlined,
} from '@ant-design/icons'
import MarkdownRenderer from '../components/MarkdownRenderer'
import LoadingSkeleton from '../components/LoadingSkeleton'
import StageLineChart from '../components/StageLineChart'
import { getLearningPath, getLearningPathById } from '../api/planner'
import { getResources, getResource } from '../api/resource'
import { getEvaluation } from '../api/evaluate'
import { shouldUseMock } from '../utils/useMock'
import { useLearningBehavior } from '../hooks/useLearningBehavior'

const USE_MOCK = shouldUseMock()

const { Title, Text, Paragraph } = Typography

// ── 常量 ──

const STUDENT_ID = 'demo-student-01'

const STATUS_CONFIG = {
  completed: {
    icon: CheckCircleFilled, color: 'var(--stage-completed)', bg: 'var(--stage-completed-bg)',
    label: '已完成', dot: 'var(--stage-completed)',
    tagColor: 'green', glow: 'none',
  },
  in_progress: {
    icon: PlayCircleFilled, color: 'var(--stage-inprogress)', bg: 'var(--stage-inprogress-bg)',
    label: '进行中', dot: 'var(--stage-inprogress)', pulse: true,
    tagColor: 'processing', glow: '0 0 0 4px var(--stage-inprogress-glow)',
  },
  locked: {
    icon: LockFilled, color: 'var(--stage-locked-dot)', bg: 'var(--stage-locked-bg)',
    label: '未解锁', dot: 'var(--stage-locked)',
    tagColor: 'default', glow: 'none',
  },
}

const TYPE_CONFIG = {
  document: { icon: <FileTextOutlined />, color: 'blue', label: '文档' },
  exercise: { icon: <EditOutlined />, color: 'green', label: '练习' },
  quiz: { icon: <QuestionCircleOutlined />, color: 'orange', label: '测验' },
  code: { icon: <CodeOutlined />, color: 'red', label: '代码' },
  mindmap: { icon: <BranchesOutlined />, color: 'purple', label: '导图' },
}

const URGENCY_CONFIG = {
  high: { color: 'var(--color-danger)', label: '高优先', icon: <WarningFilled />, tagColor: 'red' },
  medium: { color: 'var(--color-warning)', label: '中优先', icon: <ClockCircleOutlined />, tagColor: 'orange' },
  low: { color: 'var(--color-primary)', label: '低优先', icon: <CheckCircleOutlined />, tagColor: 'blue' },
}

const TASK_TYPE_ICONS = {
  study: '📖', exercise: '✏️', quiz: '📝', project: '🔨', review: '🔁',
}

const DIFFICULTY_COLORS = {
  '初级': 'green', '中级': 'blue', '高级': 'orange', '专家': 'red',
}

// ── 工具函数 ──

/**
 * 根据 stage.topics 匹配资源
 * 双向模糊匹配：resource.topic 包含 stage topic 或 stage topic 包含 resource.topic
 */
function matchResourcesToStage(stage, allResources) {
  if (!stage?.topics?.length || !allResources?.length) return []
  return allResources.filter((res) => {
    const resTopic = (res.topic || '').toLowerCase()
    if (!resTopic) return false
    return stage.topics.some((t) => {
      const topic = t.toLowerCase()
      return resTopic.includes(topic) || topic.includes(resTopic)
    })
  })
}

/** 计算 stage 的预计天数（汇总 tasks 的 estimated_hours / 2） */
function computeStageDays(stage) {
  if (stage.estimated_days != null) return stage.estimated_days
  const hours = (stage.tasks || []).reduce(
    (sum, t) => sum + (t.estimated_hours || 0.5),
    0,
  )
  return Math.max(1, Math.round(hours / 2))
}

/** 根据 stage_id 和 current_stage 计算状态 */
function getStageStatus(stage, currentStage) {
  const cur = currentStage || 1
  const id = stage.stage_id
  if (id < cur) return 'completed'
  if (id === cur) return 'in_progress'
  return 'locked'
}

/** 格式化分钟 → 可读时间 */
function formatMinutes(minutes) {
  if (!minutes || minutes <= 0) return '--'
  if (minutes < 60) return `${minutes} 分`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h} 时 ${m} 分` : `${h} 时`
}

// ── Mock 数据（开发期无后端时使用）──

const MOCK_PATH = {
  id: 'mock-path-01',
  student_id: STUDENT_ID,
  version: 1,
  goal: '掌握核心知识体系，提升解题能力',
  stages: [
    {
      stage_id: 1, title: '基础概念巩固',
      description: '回顾并巩固核心基础概念，建立知识框架',
      objectives: ['掌握基本定义和定理', '理解核心公式推导'],
      topics: ['基础概念', '核心公式'],
      tasks: [
        { task_id: '1-1', type: 'study', description: '阅读基础教材第一章', estimated_hours: 1.5, difficulty: '初级' },
        { task_id: '1-2', type: 'exercise', description: '完成基础概念练习题 5 道', estimated_hours: 2, difficulty: '初级' },
      ],
    },
    {
      stage_id: 2, title: '进阶技能训练',
      description: '在基础之上进行进阶能力训练',
      objectives: ['掌握复杂题型解题思路', '提升分析能力'],
      topics: ['进阶题型', '解题技巧'],
      tasks: [
        { task_id: '2-1', type: 'study', description: '学习进阶解题方法', estimated_hours: 2, difficulty: '中级' },
        { task_id: '2-2', type: 'quiz', description: '完成进阶测试卷一套', estimated_hours: 1.5, difficulty: '中级' },
        { task_id: '2-3', type: 'exercise', description: '专项练习 8 道', estimated_hours: 2, difficulty: '中级' },
      ],
    },
    {
      stage_id: 3, title: '综合实战演练',
      description: '综合应用所学知识解决复杂问题',
      objectives: ['融会贯通各知识点', '提升实战能力'],
      topics: ['综合应用', '实战演练'],
      tasks: [
        { task_id: '3-1', type: 'project', description: '完成综合项目实战', estimated_hours: 3, difficulty: '高级' },
        { task_id: '3-2', type: 'quiz', description: '模拟考试一次', estimated_hours: 2, difficulty: '高级' },
      ],
    },
  ],
  current_stage: 2,
  status: 'active',
  total_estimated_days: 9,
  created_at: '2026-07-10T08:00:00Z',
}

const MOCK_RESOURCES = [
  { id: 'r1', type: 'document', title: '基础概念精讲讲义', topic: '基础概念', difficulty: '初级', description: '核心定义与定理的详细讲解', tags: ['基础概念', '初级', 'document'], content: '## 基础概念精讲\n\n### 1. 核心定义\n...\n\n### 2. 定理推导\n...', created_at: '2026-07-11T08:00:00Z', createdAt: '2026-07-11T08:00:00Z' },
  { id: 'r2', type: 'exercise', title: '核心公式应用练习', topic: '核心公式', difficulty: '初级', description: '10 道核心公式应用题', tags: ['核心公式', '初级', 'exercise'], content: '## 核心公式练习\n\n1. 题目一\n2. 题目二\n...', created_at: '2026-07-11T09:00:00Z', createdAt: '2026-07-11T09:00:00Z' },
  { id: 'r3', type: 'mindmap', title: '进阶知识思维导图', topic: '进阶题型', difficulty: '中级', description: '进阶题型知识结构梳理', tags: ['进阶题型', '中级', 'mindmap'], content: '## 知识结构\n- 进阶题型\n  - 分类\n  - 解法\n...', created_at: '2026-07-12T08:00:00Z', createdAt: '2026-07-12T08:00:00Z' },
  { id: 'r4', type: 'document', title: '解题技巧手册', topic: '解题技巧', difficulty: '中级', description: '各类题型解题思路汇总', tags: ['解题技巧', '中级', 'document'], content: '## 解题技巧\n\n### 审题\n...\n\n### 分析\n...', created_at: '2026-07-12T10:00:00Z', createdAt: '2026-07-12T10:00:00Z' },
  { id: 'r5', type: 'code', title: '综合项目代码模板', topic: '综合应用', difficulty: '高级', description: '实战项目基础框架', tags: ['综合应用', '高级', 'code'], content: '```python\n# 项目模板\n...\n```', created_at: '2026-07-13T08:00:00Z', createdAt: '2026-07-13T08:00:00Z' },
]

const MOCK_EVALUATION = {
  overall_score: 78,
  overallScore: 78,
  completed_tasks: 8,
  completedTasks: 8,
  total_time: 5400,
  totalTime: 5400,
  streak_days: 4,
  streakDays: 4,
  review_plan: [
    { topic: '核心公式', urgency: 'high', due_date: '2026-07-16', reason: '当前掌握度约 58 分，距上次学习 3.5 天，遗忘曲线估算记忆保持率约 42%。', recommended_resources: ['document', 'exercise'], retention: 0.42, days_since_last_study: 3.5, estimated_minutes: 25 },
    { topic: '解题技巧', urgency: 'medium', due_date: '2026-07-18', reason: '当前掌握度约 68 分，距上次学习 2.0 天，遗忘曲线估算记忆保持率约 58%。', recommended_resources: ['reading', 'exercise'], retention: 0.58, days_since_last_study: 2.0, estimated_minutes: 20 },
    { topic: '基础概念', urgency: 'low', due_date: '2026-07-22', reason: '当前掌握度约 85 分，距上次学习 1.0 天，遗忘曲线估算记忆保持率约 78%。', recommended_resources: ['reading'], retention: 0.78, days_since_last_study: 1.0, estimated_minutes: 15 },
  ],
  reviewPlan: [],  // will be populated from review_plan
}

// ── 资源详情弹窗 ──

function ResourceDetailModal({ resource, visible, onClose, onRetry, onComplete, completing, resourceError }) {
  if (!resource && !resourceError) return null

  if (resourceError) {
    return (
      <Modal
        title="资源加载失败"
        open={visible}
        onCancel={onClose}
        footer={[
          <Button key="close" onClick={onClose}>关闭</Button>,
          <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={onRetry}>
            重试
          </Button>,
        ]}
      >
        <Result
          status="error"
          title="无法加载资源内容"
          subTitle={resourceError}
        />
      </Modal>
    )
  }

  const config = TYPE_CONFIG[resource.type] || TYPE_CONFIG.document

  return (
    <Modal
      title={
        <Space>
          <Tag icon={config.icon} color={config.color}>{config.label}</Tag>
          <Text strong style={{ fontSize: 16 }}>{resource.title}</Text>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={
        <Space>
          <Button onClick={onClose}>关闭</Button>
          {onComplete && (
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={onComplete}
              loading={completing}
            >
              完成学习
            </Button>
          )}
        </Space>
      }
      width={720}
      style={{ top: 40 }}
      styles={{ body: { maxHeight: '70vh', overflow: 'auto', padding: '20px 28px' } }}
    >
      {/* 元信息 */}
      <Space wrap style={{ marginBottom: 16 }}>
        {resource.topic && <Tag color="purple">{resource.topic}</Tag>}
        {resource.difficulty && (
          <Tag color={DIFFICULTY_COLORS[resource.difficulty] || 'default'}>
            {resource.difficulty}
          </Tag>
        )}
      </Space>

      {/* 内容 */}
      {resource.content ? (
        <MarkdownRenderer content={resource.content} />
      ) : (
        <Empty description="暂无内容" />
      )}
    </Modal>
  )
}

// ══════════════════════════════════════════════════════════════
// 主页面
// ══════════════════════════════════════════════════════════════

export default function LearningJourneyPage() {
  const navigate = useNavigate()
  const location = useLocation()

  // 从 URL 查询参数获取 pathId
  const searchParams = new URLSearchParams(location.search)
  const pathId = searchParams.get('pathId')

  // ── 数据状态 ──
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pathData, setPathData] = useState(null)
  const [resources, setResources] = useState([])
  const [evaluation, setEvaluation] = useState(null)

  // ── UI 状态 ──
  const [expandedStageId, setExpandedStageId] = useState(null)
  const [selectedResource, setSelectedResource] = useState(null)
  const [resourceModalVisible, setResourceModalVisible] = useState(false)
  const [resourceError, setResourceError] = useState(null)
  const [resourceErrors, setResourceErrors] = useState({})  // resourceId → errorMsg
  const [completing, setCompleting] = useState(false)           // 完成学习按钮 loading

  // ── 学习行为同步 Hook ──
  const { trackView, trackComplete } = useLearningBehavior((report) => {
    if (report) setEvaluation(report)
  })

  // ── 首次加载：并行读取路径、资源、评估报告 ──
  useEffect(() => {
    loadAllData()
  }, [pathId])

  async function loadAllData() {
    setLoading(true)
    setError(null)

    try {
      // 如果有 pathId，加载指定路径；否则加载当前活跃路径
      const pathPromise = pathId
        ? getLearningPathById(STUDENT_ID, pathId).catch(() => null)
        : getLearningPath(STUDENT_ID).catch(() => null)

      const [path, resList, evalReport, feed, wrongBook] = await Promise.all([
        pathPromise,
        getResources({ student_id: STUDENT_ID, page_size: 100 }).catch(() => null),
        getEvaluation(STUDENT_ID).catch(() => null),
      ])

      if (USE_MOCK) {
        setPathData(path || MOCK_PATH)
        setResources(resList?.items?.length ? resList.items : MOCK_RESOURCES)
        const ev = evalReport
        if (ev) {
          // 确保 reviewPlan 有值
          if (!ev.reviewPlan?.length && ev.review_plan?.length) {
            ev.reviewPlan = ev.review_plan
          }
        }
        setEvaluation(ev || MOCK_EVALUATION)
      } else {
        if (!path && !resList && !evalReport) {
          setError('无法连接到后端服务，请检查网络连接后重试')
        }
        setPathData(path)
        setResources(resList?.items || [])
        const ev = evalReport
        if (ev && !ev.reviewPlan?.length && ev.review_plan?.length) {
          ev.reviewPlan = ev.review_plan
        }
        setEvaluation(ev)
      }
    } catch (err) {
      if (USE_MOCK) {
        setPathData(MOCK_PATH)
        setResources(MOCK_RESOURCES)
        setEvaluation(MOCK_EVALUATION)
      } else {
        setError(err.message || '加载失败')
      }
    } finally {
      setLoading(false)
    }
  }

  // ── 点击资源 → 已有 content 则直接展示，否则调用详情接口 ──
  const handleResourceClick = useCallback(async (resource) => {
    setResourceError(null)
    setSelectedResource(resource)
    setResourceModalVisible(true)

    // 记录查看行为（内部有防抖，静默失败）
    trackView(resource)

    // 已有内容，直接展示
    if (resource.content) return

    // 调用详情接口获取 content
    try {
      const detail = await getResource(resource.id)
      if (detail) {
        setSelectedResource({ ...resource, ...detail })
        // 清除该资源的错误
        setResourceErrors((prev) => {
          const next = { ...prev }
          delete next[resource.id]
          return next
        })
      }
    } catch (err) {
      const errMsg = err.message || '加载资源详情失败'
      setResourceError(errMsg)
      setResourceErrors((prev) => ({ ...prev, [resource.id]: errMsg }))
    }
  }, [trackView])

  // 重试加载失败的资源
  const handleRetryResource = useCallback(async () => {
    if (!selectedResource) return
    setResourceError(null)
    try {
      const detail = await getResource(selectedResource.id)
      if (detail) {
        setSelectedResource({ ...selectedResource, ...detail })
        setResourceErrors((prev) => {
          const next = { ...prev }
          delete next[selectedResource.id]
          return next
        })
      }
    } catch (err) {
      const errMsg = err.message || '加载资源详情失败'
      setResourceError(errMsg)
      setResourceErrors((prev) => ({ ...prev, [selectedResource.id]: errMsg }))
    }
  }, [selectedResource])

  // 标记资源为"已完成" → 记录行为 → 触发评估刷新
  const handleCompleteResource = useCallback(async () => {
    if (!selectedResource) return
    setCompleting(true)
    try {
      await trackComplete(selectedResource)
      message.success('学习进度已更新！')
      setResourceModalVisible(false)
      setSelectedResource(null)
      setResourceError(null)
    } catch (err) {
      message.error('记录失败: ' + (err.message || '未知错误'))
    } finally {
      setCompleting(false)
    }
  }, [selectedResource, trackComplete])

  const handleCloseResourceModal = useCallback(() => {
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
            <Button type="primary" icon={<ReloadOutlined />} onClick={loadAllData}>
              重新加载
            </Button>
          }
        />
      </div>
    )
  }

  // ── 数据提取 ──
  const stages = pathData?.stages || []
  const currentStage = pathData?.current_stage || 1
  const totalTasks = stages.reduce((s, st) => s + (st.tasks?.length || 0), 0)
  const completedTasks = evaluation?.completedTasks || evaluation?.completed_tasks || 0
  const overallScore = evaluation?.overallScore || evaluation?.overall_score || 0
  const totalTime = evaluation?.totalTime || evaluation?.total_time || 0
  const streakDays = evaluation?.streakDays || evaluation?.streak_days || 0
  const reviewPlan = evaluation?.reviewPlan || evaluation?.review_plan || []

  // 当前阶段
  const currentStageData = stages.find((s) => s.stage_id === currentStage)
  const currentStageResources = matchResourcesToStage(currentStageData, resources)
  const currentStageCompleted = currentStageData?.tasks?.filter(
    (t) => t.status === 'completed',
  )?.length || 0
  const currentStageTotal = currentStageData?.tasks?.length || 0

  return (
    <div style={{ height: '100%', overflow: 'auto', background: 'var(--bg-page)', padding: '20px 24px' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* ═══ 页面标题 ═══ */}
        <div style={{ marginBottom: 20, position: 'relative' }}>
          <Button
            type="text"
            icon={<LeftOutlined />}
            onClick={() => navigate('/profile', { state: { startChat: true } })}
            style={{ position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)', zIndex: 1 }}
          >
            返回主页
          </Button>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Title level={3} style={{ margin: 0 }}>
              🗺️ {pathData?.goal || '闯关学习旅程'}
            </Title>
          </div>
          <div style={{ position: 'absolute', right: 0, top: '50%', transform: 'translateY(-50%)' }}>
            <Space wrap>
              <Button icon={<InboxOutlined />} onClick={() => navigate('/wrong-book')}>
                错题本{wrongBookCount > 0 ? `（${wrongBookCount}）` : ''}
              </Button>
            </Space>
          </div>
        </div>

        {/* ═══ 折线式闯关路径：每个拐点是一关 ═══ */}
        <Card
          title={<Text strong style={{ fontSize: 16 }}>📈 折线闯关路径</Text>}
          style={{ borderRadius: 12, marginBottom: 24 }}
          styles={{ body: { padding: '12px 16px 0' } }}
        >
          <StageLineChart
            stages={stages}
            currentStage={currentStage}
            height={360}
            onStageClick={(stage) => navigate(`/stage/${stage.stage_id}/resources`, {
              state: { stage, pathId: pathData?.id, pathData },
            })}
          />
        </Card>

        {/* ═══ 当前阶段进度 ═══ */}
        {currentStageData && (
          <Card
            style={{ marginBottom: 24, borderRadius: 12, border: '1px solid var(--stage-inprogress-border)' }}
            styles={{ body: { padding: '20px 24px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <Space size={8}>
                  <FlagFilled style={{ color: 'var(--stage-inprogress)' }} />
                  <Text strong style={{ fontSize: 16 }}>
                    当前阶段：{currentStageData.title}
                  </Text>
                  <Tag color="blue">进行中</Tag>
                </Space>
                <Paragraph type="secondary" style={{ margin: '4px 0 0', fontSize: 13 }}>
                  {currentStageData.description}
                </Paragraph>
              </div>
              <Space size={24}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>任务进度</Text>
                  <Text strong style={{ fontSize: 18 }}>
                    {currentStageCompleted}/{currentStageTotal}
                  </Text>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>匹配资源</Text>
                  <Text strong style={{ fontSize: 18, color: 'var(--color-primary)' }}>
                    {currentStageResources.length}
                  </Text>
                </div>
                <Progress
                  type="circle"
                  percent={currentStageTotal > 0 ? Math.round((currentStageCompleted / currentStageTotal) * 100) : 0}
                  size={52}
                  strokeColor={{ '0%': 'var(--color-primary)', '100%': 'var(--color-success)' }}
                />
              </Space>
            </div>
          </Card>
        )}

        {/* ═══ 主内容：阶段列表 + 复习计划 ═══ */}
        <Row gutter={[24, 24]}>
          {/* 左：阶段时间线 */}
          <Col xs={24} lg={16}>
            <Card
              title={<Text strong style={{ fontSize: 16 }}>📐 学习阶段</Text>}
              style={{ borderRadius: 12 }}
              styles={{ body: { padding: '12px 20px 20px' } }}
            >
              {stages.length === 0 ? (
                <Empty description="暂无学习阶段" />
              ) : (
                <div className="journey-stage-list">
                  {stages.map((stage, idx) => {
                    const status = getStageStatus(stage, currentStage)
                    const cfg = STATUS_CONFIG[status]
                    const Icon = cfg.icon
                    const isExpanded = expandedStageId === stage.stage_id
                    const matchedResources = matchResourcesToStage(stage, resources)
                    const stageCompleted = stage.tasks?.filter((t) => t.status === 'completed')?.length || 0
                    const stageTotal = stage.tasks?.length || 0
                    const stageDays = computeStageDays(stage)
                    const isLast = idx === stages.length - 1

                    return (
                      <div key={stage.stage_id} style={{ display: 'flex', gap: 0 }}>
                        {/* 时间线指示器 */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 40, flexShrink: 0 }}>
                          <div
                            style={{
                              width: 32, height: 32, borderRadius: '50%',
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              background: cfg.dot,
                              boxShadow: cfg.glow,
                              transition: 'box-shadow 0.3s',
                            }}
                          >
                            <Icon style={{
                              fontSize: 14,
                              color: status === 'locked' ? 'var(--stage-locked)' : '#fff',
                            }} />
                          </div>
                          {!isLast && (
                            <div style={{
                              flex: 1, width: 2, minHeight: 24,
                              background: status === 'completed' ? 'var(--stage-completed)' : 'var(--border)',
                              margin: '4px 0',
                            }} />
                          )}
                        </div>

                        {/* 阶段卡片 */}
                        <div style={{ flex: 1, paddingBottom: isLast ? 0 : 16 }}>
                          <Card
                            size="small"
                            hoverable={status !== 'locked'}
                            style={{
                              borderRadius: 10,
                              borderColor: status === 'in_progress' ? cfg.color : 'transparent',
                              background: cfg.bg,
                              opacity: status === 'locked' ? 0.55 : 1,
                              cursor: status === 'locked' ? 'default' : 'pointer',
                              transition: 'all 0.2s',
                            }}
                            onClick={() => {
                              if (status !== 'locked') {
                                setExpandedStageId(isExpanded ? null : stage.stage_id)
                              }
                            }}
                          >
                            {/* 阶段头部 */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
                              <div style={{ flex: 1, minWidth: 200 }}>
                                <Space size={8}>
                                  <Text strong style={{ fontSize: 15, color: status === 'locked' ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                                    第{stage.stage_id}阶段：{stage.title}
                                  </Text>
                                  <Tag color={cfg.tagColor}>{cfg.label}</Tag>
                                </Space>
                                <Paragraph type="secondary" style={{ margin: '4px 0 0', fontSize: 13 }}>
                                  {stage.description}
                                </Paragraph>
                              </div>
                              <Space size={16}>
                                <Tooltip title={`任务 ${stageCompleted}/${stageTotal}`}>
                                  <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
                                    📋 {stageCompleted}/{stageTotal}
                                  </Text>
                                </Tooltip>
                                <Tooltip title={`预计 ${stageDays} 天`}>
                                  <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
                                    📅 {stageDays}天
                                  </Text>
                                </Tooltip>
                                <Tooltip title={`匹配 ${matchedResources.length} 个资源`}>
                                  <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
                                    📄 {matchedResources.length}
                                  </Text>
                                </Tooltip>
                                {status !== 'locked' && (
                                  <CaretRightOutlined
                                    style={{
                                      fontSize: 12, color: 'var(--text-muted)',
                                      transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                                      transition: 'transform 0.2s',
                                    }}
                                  />
                                )}
                              </Space>
                            </div>

                            {/* 学习目标 + 知识点标签 */}
                            <div style={{ marginTop: 8 }}>
                              <Space size={4} wrap>
                                {stage.objectives?.map((obj, oi) => (
                                  <Tag key={`obj-${oi}`} icon={<AimOutlined />} color="blue" style={{ fontSize: 11 }}>
                                    {obj}
                                  </Tag>
                                ))}
                                {stage.topics?.map((topic) => (
                                  <Tag key={topic} icon={<TagsOutlined />} color="purple" style={{ fontSize: 11 }}>
                                    {topic}
                                  </Tag>
                                ))}
                              </Space>
                            </div>

                            {/* 展开：任务列表 + 匹配资源 */}
                            {isExpanded && (
                              <div style={{ marginTop: 12 }}>
                                {/* 任务列表 */}
                                {stage.tasks?.length > 0 && (
                                  <div style={{ marginBottom: 12 }}>
                                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
                                      <UnorderedListOutlined /> 学习任务（{stage.tasks.length} 项）
                                    </Text>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                      {stage.tasks.map((task) => {
                                        const diffColor = DIFFICULTY_COLORS[task.difficulty] || 'default'
                                        const isCompleted = task.status === 'completed'
                                        return (
                                          <div
                                            key={task.task_id}
                                            style={{
                                              display: 'flex', alignItems: 'center', gap: 8,
                                              padding: '5px 10px', borderRadius: 6,
                                              background: isCompleted ? 'var(--stage-completed-bg)' : 'var(--surface-secondary)',
                                              border: `1px solid ${isCompleted ? 'var(--stage-completed-border)' : 'var(--border)'}`,
                                              fontSize: 13,
                                              opacity: isCompleted ? 0.85 : 1,
                                            }}
                                          >
                                            <span>{TASK_TYPE_ICONS[task.type] || '📌'}</span>
                                            <span style={{
                                              flex: 1,
                                              textDecoration: isCompleted ? 'line-through' : 'none',
                                              color: isCompleted ? 'var(--color-text-disabled)' : 'var(--text-primary)',
                                            }}>
                                              {task.description}
                                            </span>
                                            <Tag color={diffColor} style={{ fontSize: 10, lineHeight: '16px' }}>{task.difficulty}</Tag>
                                            {task.estimated_hours != null && (
                                              <Text type="secondary" style={{ fontSize: 11, whiteSpace: 'nowrap' }}>
                                                ⏱ {task.estimated_hours}h
                                              </Text>
                                            )}
                                            {isCompleted && <CheckCircleFilled style={{ color: 'var(--color-success)', fontSize: 12 }} />}
                                          </div>
                                        )
                                      })}
                                    </div>
                                    {stageTotal > 0 && (
                                      <Progress
                                        percent={Math.round((stageCompleted / stageTotal) * 100)}
                                        size="small"
                                        style={{ marginTop: 8 }}
                                        strokeColor={stageCompleted === stageTotal ? 'var(--color-success)' : 'var(--color-primary)'}
                                      />
                                    )}
                                  </div>
                                )}

                                {/* 匹配资源 */}
                                <div>
                                  <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
                                    📄 匹配资源（{matchedResources.length} 个）
                                  </Text>
                                  {matchedResources.length === 0 ? (
                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                      该阶段暂无匹配的学习资源
                                    </Text>
                                  ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                      {matchedResources.map((res) => {
                                        const tc = TYPE_CONFIG[res.type] || TYPE_CONFIG.document
                                        const hasError = resourceErrors[res.id]
                                        return (
                                          <div
                                            key={res.id}
                                            style={{
                                              display: 'flex', alignItems: 'center', gap: 8,
                                              padding: '6px 10px', borderRadius: 6,
                                              background: 'var(--surface-secondary)',
                                              border: `1px solid ${hasError ? 'var(--color-danger)' : 'var(--border)'}`,
                                              cursor: 'pointer',
                                              transition: 'border-color 0.2s',
                                            }}
                                            onClick={(e) => {
                                              e.stopPropagation()
                                              handleResourceClick(res)
                                            }}
                                          >
                                            <Tag icon={tc.icon} color={tc.color} style={{ margin: 0, fontSize: 11 }}>{tc.label}</Tag>
                                            <span style={{ flex: 1, fontSize: 13 }}>{res.title}</span>
                                            {res.difficulty && (
                                              <Tag color={DIFFICULTY_COLORS[res.difficulty] || 'default'} style={{ fontSize: 10, lineHeight: '16px' }}>
                                                {res.difficulty}
                                              </Tag>
                                            )}
                                            {hasError ? (
                                              <Tooltip title="加载失败">
                                                <ExclamationCircleOutlined style={{ color: 'var(--color-danger)', fontSize: 13 }} />
                                              </Tooltip>
                                            ) : (
                                              <ExpandOutlined style={{ color: 'var(--text-muted)', fontSize: 12 }} />
                                            )}
                                          </div>
                                        )
                                      })}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </Card>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </Card>
          </Col>

          {/* 右：复习计划 */}
          <Col xs={24} lg={8}>
            <Card
              title={
                <Space>
                  <ClockCircleOutlined style={{ color: 'var(--color-warning)' }} />
                  <Text strong style={{ fontSize: 16 }}>📝 复习计划</Text>
                  {reviewPlan.length > 0 && (
                    <Tag color="orange">{reviewPlan.length} 项</Tag>
                  )}
                </Space>
              }
              style={{ borderRadius: 12, position: 'sticky', top: 20 }}
              styles={{ body: { padding: '12px 16px', maxHeight: 'calc(100vh - 240px)', overflow: 'auto' } }}
            >
              {reviewPlan.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '32px 16px' }}>
                  <CheckCircleOutlined style={{ fontSize: 36, color: 'var(--stage-locked-dot)', marginBottom: 12 }} />
                  <Paragraph type="secondary" style={{ margin: 0 }}>
                    暂无复习计划
                  </Paragraph>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    完成更多学习任务后，系统会自动生成复习建议
                  </Text>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {reviewPlan.map((item, i) => {
                    const uc = URGENCY_CONFIG[item.urgency] || URGENCY_CONFIG.medium
                    return (
                      <Card
                        key={i}
                        size="small"
                        style={{
                          borderRadius: 8,
                          borderLeft: `3px solid ${uc.color}`,
                        }}
                      >
                        {/* 优先级标签 + 主题 */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                          <Text strong style={{ fontSize: 14 }}>{item.topic}</Text>
                          <Tag color={uc.tagColor} icon={uc.icon} style={{ margin: 0 }}>
                            {uc.label}
                          </Tag>
                        </div>

                        {/* 原因 */}
                        <Paragraph
                          type="secondary"
                          style={{ fontSize: 12, marginBottom: 8, lineHeight: 1.5 }}
                          ellipsis={{ rows: 2, expandable: true, symbol: '展开' }}
                        >
                          {item.reason}
                        </Paragraph>

                        {/* 详情 */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, fontSize: 12 }}>
                          {item.due_date && (
                            <Text type="secondary">
                              📅 {item.due_date}
                            </Text>
                          )}
                          {item.estimated_minutes != null && (
                            <Text type="secondary">
                              ⏱ {formatMinutes(item.estimated_minutes)}
                            </Text>
                          )}
                          {item.retention != null && (
                            <Tooltip title="记忆保持率">
                              <Text
                                type="secondary"
                                style={{
                                  color: item.retention < 0.5 ? 'var(--color-danger)' : item.retention < 0.7 ? 'var(--color-warning)' : 'var(--color-success)',
                                }}
                              >
                                🧠 {Math.round(item.retention * 100)}%
                              </Text>
                            </Tooltip>
                          )}
                        </div>

                        {/* 推荐资源类型 */}
                        {item.recommended_resources?.length > 0 && (
                          <div style={{ marginTop: 6 }}>
                            <Space size={4} wrap>
                              {item.recommended_resources.map((rt) => {
                                const tc = TYPE_CONFIG[rt]
                                return tc ? (
                                  <Tag key={rt} icon={tc.icon} color={tc.color} style={{ fontSize: 11, margin: 0 }}>
                                    {tc.label}
                                  </Tag>
                                ) : null
                              })}
                            </Space>
                          </div>
                        )}
                      </Card>
                    )
                  })}
                </div>
              )}
            </Card>
          </Col>
        </Row>

        {/* ═══ 底部：学习时长 + 整体进度 ═══ */}
        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col xs={24} sm={12}>
            <Card size="small" style={{ borderRadius: 10 }}>
              <Statistic
                title="累计学习时长"
                value={formatMinutes(Math.round(totalTime / 60))}
                prefix={<ClockCircleOutlined style={{ color: 'var(--color-primary)' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12}>
            <Card size="small" style={{ borderRadius: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <BookOutlined style={{ fontSize: 24, color: 'var(--color-purple)' }} />
                <div style={{ flex: 1 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>整体进度</Text>
                  <Progress
                    percent={totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0}
                    strokeColor={{ '0%': 'var(--color-primary)', '100%': 'var(--color-success)' }}
                    style={{ marginBottom: 0 }}
                  />
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      </div>

      {/* 资源详情弹窗 */}
      <ResourceDetailModal
        resource={selectedResource}
        visible={resourceModalVisible}
        onClose={handleCloseResourceModal}
        onRetry={handleRetryResource}
        onComplete={handleCompleteResource}
        completing={completing}
        resourceError={resourceError}
      />
    </div>
  )
}
