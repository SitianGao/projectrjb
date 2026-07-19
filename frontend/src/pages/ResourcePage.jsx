import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Button,
  Card,
  Col,
  DatePicker,
  Empty,
  Input,
  Result,
  Row,
  Select,
  Skeleton,
  Space,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  BookOutlined,
  BranchesOutlined,
  CodeOutlined,
  EditOutlined,
  ExperimentOutlined,
  FilePptOutlined,
  FileTextOutlined,
  ReloadOutlined,
  RightOutlined,
  RobotOutlined,
  SearchOutlined,
  SoundOutlined,
  StarFilled,
  StarOutlined,
} from '@ant-design/icons'
import { bookmarkResource } from '../api/resource'
import { useAuth } from '../contexts/AuthContext'
import { useResources } from '../hooks/useResources'
import {
  getResourceSourceLabel,
  getResourceStats,
  getTriggerReasonLabel,
  isTargetedResource,
  learningStatusLabel,
  normalizeTitle,
} from '../utils/resourceNormalizer'
import './ResourcePage.css'

const { Paragraph, Text, Title } = Typography
const { RangePicker } = DatePicker

const TYPE_CONFIG = {
  document: { icon: <FileTextOutlined />, color: 'blue', label: '讲义' },
  exercise: { icon: <EditOutlined />, color: 'green', label: '练习题' },
  code: { icon: <CodeOutlined />, color: 'red', label: '代码' },
  mindmap: { icon: <BranchesOutlined />, color: 'purple', label: '思维导图' },
  ppt: { icon: <FilePptOutlined />, color: 'magenta', label: 'PPT' },
  audio: { icon: <SoundOutlined />, color: 'geekblue', label: '音频' },
  interactive_classroom: { icon: <ExperimentOutlined />, color: 'purple', label: 'AI 互动课堂' },
  reading: { icon: <BookOutlined />, color: 'cyan', label: '阅读' },
}

const TRIGGER_OPTIONS = [
  { label: '当前学习任务', value: 'learning_task' },
  { label: '近期学习诊断', value: 'evaluation' },
  { label: '错题', value: 'wrong_book' },
  { label: 'AI 学习助手', value: 'tutor' },
  { label: '路径调整', value: 'path_adjustment' },
  { label: '自主生成', value: 'manual_workspace' },
  { label: '课程预置', value: 'curated_course' },
]

const SPECIAL_GROUPS = [
  ['evaluation', '评估诊断生成'],
  ['wrong_book', '错题生成'],
  ['tutor', 'AI 学习助手生成'],
  ['path_adjustment', '路径调整生成'],
]

function resourceTime(resource, field = 'createdAt') {
  const value = field === 'createdAt'
    ? resource.createdAt || resource.created_at
    : resource.user_state?.[field]
  const time = value ? new Date(value).getTime() : 0
  return Number.isFinite(time) ? time : 0
}

export default function ResourcePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { courses, activeCourse } = useAuth()
  const [activeTab, setActiveTab] = useState('overview')
  const [keyword, setKeyword] = useState('')
  const [courseId, setCourseId] = useState(() => searchParams.get('courseId') || undefined)
  const [stageId, setStageId] = useState()
  const [resourceType, setResourceType] = useState()
  const [triggerSource, setTriggerSource] = useState()
  const [learningStatus, setLearningStatus] = useState()
  const [sourceLabel, setSourceLabel] = useState()
  const [timeRange, setTimeRange] = useState([])
  const [sort, setSort] = useState('recent')

  const { data: resources, loading, error, reload } = useResources({
    keyword: keyword || undefined,
    courseId,
    stageId,
    type: resourceType,
    triggerSource,
    learningStatus,
    sort,
    createdFrom: timeRange?.[0]?.startOf('day').toISOString(),
    createdTo: timeRange?.[1]?.endOf('day').toISOString(),
  })

  const visibleResources = useMemo(
    () => sourceLabel
      ? resources.filter((item) => getResourceSourceLabel(item) === sourceLabel)
      : resources,
    [resources, sourceLabel],
  )

  const stageOptions = useMemo(() => {
    const values = new Map()
    resources.forEach((item) => {
      if (item.stage_id) values.set(item.stage_id, item.stage_title || `阶段 ${item.stage_id}`)
    })
    return [...values].map(([value, label]) => ({ value, label }))
  }, [resources])

  const recentOpened = useMemo(
    () => [...visibleResources]
      .filter((item) => item.user_state?.last_opened_at)
      .sort((a, b) => resourceTime(b, 'last_opened_at') - resourceTime(a, 'last_opened_at')),
    [visibleResources],
  )
  const recentGenerated = useMemo(
    () => [...visibleResources].sort((a, b) => resourceTime(b) - resourceTime(a)),
    [visibleResources],
  )
  const recentCompleted = useMemo(
    () => [...visibleResources]
      .filter((item) => item.user_state?.learning_status === 'completed')
      .sort((a, b) => resourceTime(b, 'completed_at') - resourceTime(a, 'completed_at')),
    [visibleResources],
  )
  const continueItems = useMemo(
    () => visibleResources.filter((item) => item.user_state?.learning_status === 'in_progress'),
    [visibleResources],
  )

  const courseGroups = useMemo(() => {
    const groups = new Map()
    visibleResources.forEach((resource) => {
      const courseKey = resource.course_id || 'unassigned'
      const stageKey = resource.stage_id || 'unassigned'
      const taskKey = resource.task_id || 'unassigned'
      if (!groups.has(courseKey)) {
        groups.set(courseKey, {
          title: resource.course_title || '未关联课程',
          stages: new Map(),
        })
      }
      const course = groups.get(courseKey)
      if (!course.stages.has(stageKey)) {
        course.stages.set(stageKey, {
          title: resource.stage_title || '未关联阶段',
          tasks: new Map(),
        })
      }
      const stage = course.stages.get(stageKey)
      if (!stage.tasks.has(taskKey)) {
        stage.tasks.set(taskKey, {
          title: resource.task_title || '自由学习资料',
          resources: [],
        })
      }
      stage.tasks.get(taskKey).resources.push(resource)
    })
    return groups
  }, [visibleResources])

  async function toggleFavorite(resource) {
    try {
      await bookmarkResource(resource.id)
      await reload()
    } catch (err) {
      message.error(err.message || '收藏状态更新失败')
    }
  }

  function openResource(resource) {
    if (resource.type === 'interactive_classroom') {
      const classroomId = resource.classroom_id || resource.classroomId
      if (classroomId && resource.course_id) {
        navigate(`/course/${resource.course_id}/classroom/${classroomId}`)
        return
      }
    }
    navigate(`/resources/${resource.id}`)
  }

  const filterBar = (
    <Card className="resource-filter-card" styles={{ body: { padding: 16 } }}>
      <Space size={10} wrap>
        <Input
          allowClear
          prefix={<SearchOutlined />}
          placeholder="搜索名称、主题和知识点"
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
          style={{ width: 240 }}
        />
        <Select
          allowClear
          placeholder="全部课程"
          value={courseId}
          onChange={(value) => { setCourseId(value); setStageId(undefined) }}
          options={(courses || []).map((course) => ({ label: course.title, value: course.id }))}
          style={{ width: 150 }}
        />
        <Select allowClear placeholder="全部阶段" value={stageId} onChange={setStageId} options={stageOptions} style={{ width: 150 }} />
        <Select
          allowClear
          placeholder="资源类型"
          value={resourceType}
          onChange={setResourceType}
          options={Object.entries(TYPE_CONFIG).map(([value, config]) => ({ value, label: config.label }))}
          style={{ width: 130 }}
        />
        <Select allowClear placeholder="生成原因" value={triggerSource} onChange={setTriggerSource} options={TRIGGER_OPTIONS} style={{ width: 150 }} />
        <Select
          allowClear
          placeholder="内容来源"
          value={sourceLabel}
          onChange={setSourceLabel}
          options={['课程精选', 'AI 个性化生成', '知识库基础版', '基础提纲', '历史资源'].map((value) => ({ value, label: value }))}
          style={{ width: 150 }}
        />
        <Select
          allowClear
          placeholder="学习状态"
          value={learningStatus}
          onChange={setLearningStatus}
          options={[
            { label: '未开始', value: 'not_started' },
            { label: '学习中', value: 'in_progress' },
            { label: '已完成', value: 'completed' },
          ]}
          style={{ width: 120 }}
        />
        <RangePicker value={timeRange} onChange={(value) => setTimeRange(value || [])} />
        <Select
          value={sort}
          onChange={setSort}
          options={[
            { label: '最近生成', value: 'recent' },
            { label: '最近打开', value: 'used' },
            { label: '最近完成', value: 'completed' },
            { label: '名称排序', value: 'name' },
          ]}
          style={{ width: 120 }}
        />
        <Button icon={<ReloadOutlined />} onClick={reload} aria-label="重新加载" />
      </Space>
    </Card>
  )

  function renderGrid(items, emptyText = '暂无学习资料') {
    if (!items.length) return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} />
    return (
      <Row gutter={[14, 14]}>
        {items.map((resource) => (
          <Col xs={24} sm={12} lg={8} xl={6} key={resource.id}>
            <ResourceCard
              resource={resource}
              onOpen={() => openResource(resource)}
              onFavorite={() => toggleFavorite(resource)}
            />
          </Col>
        ))}
      </Row>
    )
  }

  function renderOverview() {
    const summaries = [
      ['最近打开', recentOpened[0], '还没有打开过资料'],
      ['最近生成', recentGenerated[0], '还没有生成资料'],
      ['最近完成', recentCompleted[0], '还没有完成资料'],
      ['继续学习', continueItems[0], '当前没有进行中的资料'],
    ]
    return (
      <div className="resource-section-stack">
        <section>
          <Title level={4}>最近学习</Title>
          <Row gutter={[14, 14]}>
            {summaries.map(([label, resource, emptyText]) => (
              <Col xs={24} sm={12} xl={6} key={label}>
                <RecentSummary
                  label={label}
                  resource={resource}
                  emptyText={emptyText}
                  onOpen={() => resource && openResource(resource)}
                />
              </Col>
            ))}
          </Row>
        </section>
        <section>
          <Title level={4}>为我生成的专项资料</Title>
          {renderGrid(visibleResources.filter(isTargetedResource).slice(0, 8), '完成学习诊断、错题复习或 AI 对话后，专项资料会出现在这里')}
        </section>
        <section>
          <Title level={4}>收藏内容</Title>
          {renderGrid(visibleResources.filter((item) => item.user_state?.is_favorite).slice(0, 4), '还没有收藏内容')}
        </section>
      </div>
    )
  }

  function renderByCourse() {
    if (!courseGroups.size) return <Empty description="暂无按课程归档的资料" />
    return (
      <div className="resource-course-tree">
        {[...courseGroups.entries()].map(([courseKey, course]) => (
          <section key={courseKey} className="resource-course-section">
            <Title level={4}>{course.title}</Title>
            {[...course.stages.entries()].map(([stageKey, stage]) => (
              <div key={stageKey} className="resource-stage-section">
                <Text strong>{stage.title}</Text>
                {[...stage.tasks.entries()].map(([taskKey, task]) => (
                  <div key={taskKey} className="resource-task-section">
                    <div className="resource-task-heading">
                      <Text>{task.title}</Text>
                      <Tag>{task.resources.length} 项资料</Tag>
                    </div>
                    {renderGrid(task.resources)}
                  </div>
                ))}
              </div>
            ))}
          </section>
        ))}
      </div>
    )
  }

  function renderTargeted() {
    const groups = SPECIAL_GROUPS.map(([source, title]) => [
      source,
      title,
      visibleResources.filter((item) => item.trigger_source === source),
    ])
    return (
      <div className="resource-section-stack">
        {groups.map(([source, title, items]) => (
          <section key={source}>
            <Title level={4}>{title}</Title>
            {renderGrid(items, `暂无${title}`)}
          </section>
        ))}
      </div>
    )
  }

  const tabItems = [
    { key: 'overview', label: '概览', children: renderOverview() },
    { key: 'by-course', label: '按课程与阶段', children: renderByCourse() },
    { key: 'targeted', label: '专项资料', children: renderTargeted() },
    {
      key: 'favorites',
      label: '收藏',
      children: renderGrid(visibleResources.filter((item) => item.user_state?.is_favorite), '还没有收藏内容'),
    },
    { key: 'history', label: '历史资料', children: renderGrid(visibleResources) },
  ]

  return (
    <div className="resource-library-page">
      <div className="resource-library-container">
        <header className="resource-library-header">
          <div>
            <Title level={3}>我的学习资料</Title>
            <Text type="secondary">搜索、收藏和回看学习过程中自动沉淀的内容</Text>
          </div>
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={() => navigate(activeCourse?.id ? `/course/${activeCourse.id}/ai-workspace` : '/ai-workspace')}
          >
            AI 学习工作台
          </Button>
        </header>

        {filterBar}

        {loading ? (
          <Skeleton active paragraph={{ rows: 8 }} />
        ) : error ? (
          <Result
            status="error"
            title="学习资料加载失败"
            subTitle={error}
            extra={<Button type="primary" onClick={reload}>重新加载</Button>}
          />
        ) : visibleResources.length === 0 ? (
          <Empty
            description="还没有符合条件的学习资料"
          >
            <Button
              type="primary"
              onClick={() => navigate(activeCourse?.id ? `/course/${activeCourse.id}/path` : '/courses')}
            >
              前往学习路径
            </Button>
          </Empty>
        ) : (
          <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
        )}
      </div>
    </div>
  )
}

function ResourceCard({ resource, onOpen, onFavorite }) {
  const config = TYPE_CONFIG[resource.type] || TYPE_CONFIG.document
  const stats = getResourceStats(resource)
  const status = resource.user_state?.learning_status || 'not_started'
  return (
    <Card className="resource-library-card" hoverable onClick={onOpen}>
      <div className="resource-card-tags">
        <Tag icon={config.icon} color={config.color}>{config.label}</Tag>
        <Tag color={status === 'completed' ? 'success' : status === 'in_progress' ? 'processing' : 'default'}>
          {learningStatusLabel(status)}
        </Tag>
      </div>
      <Text strong className="resource-card-title">
        {normalizeTitle(resource.title, resource.type, resource.topic)}
      </Text>
      <Paragraph type="secondary" ellipsis={{ rows: 2 }}>
        {[resource.course_title, resource.stage_title, resource.task_title].filter(Boolean).join(' · ') || resource.topic}
      </Paragraph>
      <Space size={6} wrap>
        <Tag>{getResourceSourceLabel(resource)}</Tag>
        <Tag color="purple">{getTriggerReasonLabel(resource)}</Tag>
      </Space>
      <div className="resource-card-footer">
        <Text type="secondary">{stats?.label || '学习资料'}</Text>
        <Space size={2}>
          <Button
            type="text"
            aria-label={resource.user_state?.is_favorite ? '取消收藏' : '收藏'}
            icon={resource.user_state?.is_favorite ? <StarFilled className="resource-favorite-icon" /> : <StarOutlined />}
            onClick={(event) => { event.stopPropagation(); onFavorite() }}
          />
          <Button type="text" aria-label="查看详情" icon={<RightOutlined />} />
        </Space>
      </div>
    </Card>
  )
}

function RecentSummary({ label, resource, emptyText, onOpen }) {
  return (
    <Card className="resource-recent-card">
      <Text type="secondary">{label}</Text>
      {resource ? (
        <>
          <Text strong className="resource-recent-title">
            {normalizeTitle(resource.title, resource.type, resource.topic)}
          </Text>
          <Text type="secondary" ellipsis>
            {resource.course_title || '学习资料'} · {getTriggerReasonLabel(resource)}
          </Text>
          <Button type="link" onClick={onOpen}>
            {label === '继续学习' ? '继续学习' : '查看资料'} <RightOutlined />
          </Button>
        </>
      ) : (
        <Text type="secondary" className="resource-recent-empty">{emptyText}</Text>
      )}
    </Card>
  )
}
