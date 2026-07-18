import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import {
  Typography, Card, Tag, Button, Space, Row, Col, Result, Empty,
  Progress, message, Spin, Modal,
} from 'antd'
import {
  ArrowLeftOutlined,
  UnorderedListOutlined, BookOutlined, ClockCircleOutlined,
  TrophyOutlined, FlagFilled, ReloadOutlined, ThunderboltOutlined,
  PlayCircleFilled, LockFilled, CheckCircleFilled,
  FileTextOutlined, RightOutlined, BranchesOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'
import MarkdownRenderer from '../components/MarkdownRenderer'
import LoadingSkeleton from '../components/LoadingSkeleton'
import ResourceGenerateDrawer from '../components/ResourceGenerateDrawer'
import { getLearningPath, getLearningPathById } from '../api/planner'
import { getResources, getResource } from '../api/resource'
import { useAuth } from '../contexts/AuthContext'
import { normalizeStringList, normalizeTasks, getStageStatus, computeStageDays } from '../utils/stageUtils'
import { safeProgress, dedupeResources } from '../utils/safeClamp'
import ClassroomResourceCard from '../components/classroom/ClassroomResourceCard'
import './StageResourcePage.css'

const { Title, Text, Paragraph } = Typography

const TYPE_CONFIG = {
  document: { icon: <FileTextOutlined />, color: 'blue', label: '讲义' },
  exercise: { icon: <FileTextOutlined />, color: 'green', label: '练习' },
  code: { icon: <FileTextOutlined />, color: 'red', label: '代码' },
  mindmap: { icon: <BranchesOutlined />, color: 'purple', label: '导图' },
  ppt: { icon: <FileTextOutlined />, color: 'magenta', label: 'PPT' },
  audio: { icon: <FileTextOutlined />, color: 'geekblue', label: '音频' },
  reading: { icon: <BookOutlined />, color: 'cyan', label: '阅读' },
  interactive_classroom: { icon: <ExperimentOutlined />, color: 'purple', label: 'AI 互动课堂' },
}

const STATUS_CONFIG = {
  completed: { icon: <CheckCircleFilled />, color: '#22C55E', label: '已完成', dot: '#22C55E' },
  current: { icon: <PlayCircleFilled />, color: '#6C5CE7', label: '进行中', dot: '#6C5CE7' },
  locked: { icon: <LockFilled />, color: 'var(--text-muted)', label: '未解锁', dot: 'var(--text-muted)' },
}

const TASK_STATUS_COLORS = {
  completed: { color: '#22C55E', bg: 'var(--stage-completed-bg)' },
  in_progress: { color: '#6C5CE7', bg: 'var(--tint-primary)' },
  pending: { color: 'var(--text-muted)', bg: 'var(--surface-secondary)' },
  locked: { color: 'var(--text-muted)', bg: 'var(--surface-secondary)' },
}

export default function StageResourcePage() {
  const { courseId, stageId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { studentId, activeCourse, courses } = useAuth()

  const navState = location.state || {}
  const requestedPathId = new URLSearchParams(location.search).get('pathId') || navState.pathId || null

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pathData, setPathData] = useState(null)
  const [stage, setStage] = useState(navState.stage || null)
  const [stageResources, setStageResources] = useState([])
  const [genDrawerOpen, setGenDrawerOpen] = useState(false)
  const [genContext, setGenContext] = useState({ source: 'stage' })

  const [selectedResource, setSelectedResource] = useState(null)
  const [resourceModalVisible, setResourceModalVisible] = useState(false)
  const [resourceLoading, setResourceLoading] = useState(false)

  const currentCourse = useMemo(() => {
    if (courseId && courses?.length) {
      return courses.find((c) => String(c.id) === String(courseId)) || activeCourse
    }
    return activeCourse
  }, [courseId, courses, activeCourse])

  useEffect(() => { loadData() }, [stageId, requestedPathId, studentId])

  async function loadData() {
    setLoading(true); setError(null)
    try {
      if (!studentId) throw new Error('课程上下文不存在')
      const path = requestedPathId ? await getLearningPathById(studentId, requestedPathId) : await getLearningPath(studentId)
      setPathData(path)

      const found = path?.stages?.find((s) => String(s.stage_id) === String(stageId))
      if (!found) { setError(`未找到阶段 ${stageId}`); setLoading(false); return }
      setStage(found)

      const resList = await getResources({ student_id: studentId, path_id: path.id, page_size: 100 })
      const allResources = resList?.items || []
      setStageResources(dedupeResources(allResources.filter((r) => {
        if (r.stage_id != null) return String(r.stage_id) === String(stageId)
        const topics = normalizeStringList(found?.topics)
        if (!topics.length) return false
        const resTopic = (r.topic || '').toLowerCase()
        return topics.some((t) => resTopic.includes(t.toLowerCase()) || t.toLowerCase().includes(resTopic))
      })))
    } catch (err) { setError(err.message || '加载失败') }
    finally { setLoading(false) }
  }

  const handleResourceClick = useCallback(async (resource) => {
    setSelectedResource(resource); setResourceModalVisible(true)
    if (resource.content) return
    setResourceLoading(true)
    try { const detail = await getResource(resource.id); if (detail) setSelectedResource({ ...resource, ...detail }) }
    catch (err) { message.error('加载资源失败') }
    finally { setResourceLoading(false) }
  }, [])

  const currentStage = pathData?.current_stage || 1
  const status = stage ? getStageStatus(stage, currentStage) : 'current'
  const statusCfg = STATUS_CONFIG[status] || STATUS_CONFIG.current
  const tasks = normalizeTasks(stage?.tasks)
  const completed = tasks.filter((t) => t.status === 'completed').length
  const { percent } = safeProgress(completed, tasks.length)
  const days = computeStageDays(stage)

  const pathUrl = courseId ? `/course/${courseId}/path` : '/journey'
  const classroomTask = tasks.find((task) => (
    /interactive_classroom|classroom|openmaic/.test(String(task.type || task.resource_type || '').toLowerCase())
  ))
  const targetCourseId = courseId || currentCourse?.id
  const enterClassroom = () => {
    if (!targetCourseId) {
      message.warning('请先选择课程')
      return
    }
    navigate(`/course/${targetCourseId}/learn/${encodeURIComponent(classroomTask?.task_id || classroomTask?.id || 'task_gradient_classroom')}`)
  }
  const generateClassroom = () => {
    setGenContext({
      source: 'stage',
      courseId: targetCourseId,
      stageId: stage?.stage_id,
      taskId: classroomTask?.task_id || classroomTask?.id || 'task_gradient_classroom',
      topic: normalizeStringList(stage?.topics)[0] || stage?.title || '梯度下降',
      types: ['interactive_classroom'],
    })
    setGenDrawerOpen(true)
  }

  if (loading) return <div style={{ height: '100%', background: 'var(--bg-page)' }}><LoadingSkeleton type="detail" /></div>

  if (error) {
    return (
      <div style={{ maxWidth: 500, margin: '60px auto', background: 'var(--bg-page)', padding: 24 }}>
        <Result status="error" title="加载失败" subTitle={error}
          extra={<Space><Button icon={<ArrowLeftOutlined />} onClick={() => navigate(pathUrl)}>返回学习路径</Button>
          <Button type="primary" icon={<ReloadOutlined />} onClick={loadData}>重试</Button></Space>} />
      </div>
    )
  }

  if (!stage) {
    return (
      <div style={{ maxWidth: 500, margin: '60px auto', background: 'var(--bg-page)', padding: 24 }}>
        <Result status="404" title="当前学习阶段不存在或已被删除"
          extra={<Button type="primary" icon={<ArrowLeftOutlined />} onClick={() => navigate(pathUrl)}>返回学习路径</Button>} />
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100%', background: 'var(--bg-page)', padding: '20px 24px 48px' }}>
      <div style={{ maxWidth: 1060, margin: '0 auto' }}>

        <Button type="text" icon={<ArrowLeftOutlined />}
          onClick={() => navigate(pathUrl)} style={{ marginBottom: 16, paddingLeft: 0 }}>
          返回学习路径
        </Button>

        {/* ── Stage Header ── */}
        <Card style={{ borderRadius: 16, marginBottom: 24, borderLeft: `4px solid ${statusCfg.color}`, border: `1px solid var(--border)` }}
          styles={{ body: { padding: '24px 28px' } }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <Space size={8} style={{ marginBottom: 8 }}>
                <FlagFilled style={{ color: statusCfg.color, fontSize: 18 }} />
                <Title level={3} style={{ margin: 0, color: 'var(--text-primary)' }}>
                  {stage.title}
                </Title>
                <Tag color={status === 'current' ? 'purple' : status === 'completed' ? 'success' : 'default'} style={{ borderRadius: 6 }}>
                  {statusCfg.label}
                </Tag>
              </Space>
            </div>
            <Space size={24}>
              <div style={{ textAlign: 'center' }}><Text type="secondary" style={{ fontSize: 11, display: 'block' }}>任务进度</Text>
                <Text strong style={{ fontSize: 18 }}>{completed}/{tasks.length}</Text></div>
              <div style={{ textAlign: 'center' }}><Text type="secondary" style={{ fontSize: 11, display: 'block' }}>推荐资源</Text>
                <Text strong style={{ fontSize: 18, color: '#6C5CE7' }}>{stageResources.length}</Text></div>
              <Progress type="circle" percent={percent} size={52} strokeColor="#6C5CE7" />
            </Space>
          </div>

          {/* Stats row */}
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={12} sm={6}><Stat title="学习任务" value={`${tasks.length} 项`} icon={<UnorderedListOutlined style={{ color: '#6C5CE7' }} />} /></Col>
            <Col xs={12} sm={6}><Stat title="预计天数" value={`${days} 天`} icon={<ClockCircleOutlined style={{ color: '#F59E0B' }} />} /></Col>
            <Col xs={12} sm={6}><Stat title="已完成" value={`${completed} / ${tasks.length}`} icon={<TrophyOutlined style={{ color: '#22C55E' }} />} /></Col>
            <Col xs={12} sm={6}><Stat title="推荐资源" value={`${stageResources.length} 项`} icon={<BookOutlined style={{ color: '#6C5CE7' }} />} /></Col>
          </Row>
        </Card>

        {/* ── Task List ── */}
        {tasks.length > 0 && (
          <Card title={<Space><UnorderedListOutlined /><Text strong>学习任务（{tasks.length} 项）</Text></Space>}
            style={{ borderRadius: 16, marginBottom: 24, border: '1px solid var(--border)' }}
            styles={{ body: { padding: '14px 20px 20px' } }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {tasks.map((task) => {
                const taskStatus = task.status === 'completed' ? 'completed' : task.status === 'active' ? 'in_progress' : 'pending'
                const tc = TASK_STATUS_COLORS[taskStatus] || TASK_STATUS_COLORS.pending
                return (
                  <div key={task.task_id} style={{
                    display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderRadius: 8,
                    background: tc.bg, border: `1px solid var(--border)`,
                  }}>
                    <span style={{ flex: 1, fontSize: 13, color: 'var(--text-primary)' }}>{task.description}</span>
                    {task.difficulty && <Tag style={{ borderRadius: 6, fontSize: 11 }}>{task.difficulty}</Tag>}
                    {task.estimated_hours != null && <Text type="secondary" style={{ fontSize: 11 }}>⏱ {task.estimated_hours}h</Text>}
                    {/interactive_classroom|classroom|openmaic/.test(String(task.type || task.resource_type || '').toLowerCase()) ? (
                      <Button size="small" type="primary" icon={<ExperimentOutlined />} onClick={enterClassroom} style={{ borderRadius: 6, background: '#6C5CE7' }}>
                        进入课堂
                      </Button>
                    ) : taskStatus === 'completed' ? <CheckCircleFilled style={{ color: '#22C55E' }} /> :
                     taskStatus === 'in_progress' ? <Button size="small" type="primary" style={{ borderRadius: 6, background: '#6C5CE7' }}>进行中</Button> :
                     <Button size="small" style={{ borderRadius: 6 }}>开始任务</Button>}
                  </div>
                )
              })}
            </div>
            {tasks.length > 0 && <Progress percent={percent} style={{ marginTop: 10 }} strokeColor="#6C5CE7" />}
          </Card>
        )}

        <div style={{ marginBottom: 24 }}>
          <ClassroomResourceCard
            title="OpenMAIC 梯度下降互动课堂"
            description="在当前阶段中完成讲授、学习率模拟、TutorAgent 实时讲解、知识检查和课堂总结。"
            onEnter={enterClassroom}
            onGenerate={generateClassroom}
          />
        </div>

        {/* ── Recommended Resources ── */}
        <Card
          title={<Space><BookOutlined /><Text strong>推荐学习资源（{stageResources.length} 项）</Text></Space>}
          extra={<Space>
            <Button icon={<ThunderboltOutlined />} type="primary" size="small"
              onClick={() => {
                setGenContext({
                  source: 'stage',
                  courseId: targetCourseId,
                  stageId: stage?.stage_id,
                  topic: normalizeStringList(stage?.topics)[0] || stage?.title || '',
                })
                setGenDrawerOpen(true)
              }}
              style={{ borderRadius: 8, background: '#6C5CE7', borderColor: '#6C5CE7' }}>
              为本阶段生成资源
            </Button>
            <Button size="small" onClick={() => navigate(`/resources?stageId=${stageId}`)}
              style={{ borderRadius: 8 }}>进入资源中心 <RightOutlined /></Button>
          </Space>}
          style={{ borderRadius: 16, border: '1px solid var(--border)' }}
          styles={{ body: { padding: '16px 20px 20px' } }}>
          {stageResources.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <BookOutlined style={{ fontSize: 36, color: 'var(--text-muted)', marginBottom: 12 }} />
              <Paragraph style={{ color: 'var(--text-secondary)', maxWidth: 400, margin: '0 auto 16px' }}>
                本阶段暂无学习资源。系统可以根据当前阶段目标和知识点，为你生成讲义、练习题、PPT 或思维导图。
              </Paragraph>
              <Space>
                <Button type="primary" icon={<ThunderboltOutlined />}
                  onClick={() => {
                    setGenContext({
                      source: 'stage',
                      courseId: targetCourseId,
                      stageId: stage?.stage_id,
                      topic: normalizeStringList(stage?.topics)[0] || stage?.title || '',
                    })
                    setGenDrawerOpen(true)
                  }}
                  style={{ borderRadius: 8, background: '#6C5CE7' }}>为本阶段生成资源</Button>
                <Button onClick={() => navigate('/resources')} style={{ borderRadius: 8 }}>进入资源中心</Button>
              </Space>
            </div>
          ) : (
            <Row gutter={[12, 12]}>
              {stageResources.slice(0, 4).map((res) => {
                const cfg = TYPE_CONFIG[res.type] || TYPE_CONFIG.document
                return (
                  <Col xs={24} sm={12} md={6} key={res.id}>
                    <Card size="small" hoverable style={{ borderRadius: 10, border: '1px solid var(--border)', minWidth: 0 }}
                      onClick={() => handleResourceClick(res)}
                      styles={{ body: { padding: '12px 14px' } }}>
                      <Tag icon={cfg.icon} color={cfg.color} style={{ borderRadius: 6, marginBottom: 6 }}>{cfg.label}</Tag>
                      <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 4 }} ellipsis={{ rows: 2 }}>{res.title}</Text>
                      {res.difficulty && <Text type="secondary" style={{ fontSize: 11 }}>{res.difficulty}</Text>}
                    </Card>
                  </Col>
                )
              })}
            </Row>
          )}
          {stageResources.length > 4 && (
            <Button type="link" onClick={() => navigate(`/resources?stageId=${stageId}`)} style={{ padding: 0, marginTop: 12 }}>
              查看本阶段全部资源 <RightOutlined />
            </Button>
          )}
        </Card>
      </div>

      {/* ── Generate Drawer (auto-filled with stage context) ── */}
      <ResourceGenerateDrawer
        visible={genDrawerOpen}
        onClose={() => setGenDrawerOpen(false)}
        onGenerated={() => { loadData(); setGenDrawerOpen(false) }}
        context={genContext}
      />

      {/* ── Resource Detail Modal ── */}
      <Modal title={selectedResource?.title} open={resourceModalVisible}
        onCancel={() => { setResourceModalVisible(false); setSelectedResource(null) }}
        footer={<Button onClick={() => { setResourceModalVisible(false); setSelectedResource(null) }}>关闭</Button>}
        width={720} styles={{ body: { maxHeight: '65vh', overflow: 'auto', padding: '20px 28px' } }}>
        {resourceLoading ? <Spin /> : selectedResource?.content ? <MarkdownRenderer content={selectedResource.content} /> : <Empty description="暂无内容" />}
      </Modal>
    </div>
  )
}

function Stat({ title, value, icon }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      {icon}
      <div><Text type="secondary" style={{ fontSize: 11, display: 'block' }}>{title}</Text>
      <Text strong style={{ fontSize: 14 }}>{value}</Text></div>
    </div>
  )
}
