import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Empty, Result, Spin, Tag, Typography, Space, Descriptions, message } from 'antd'
import {
  ArrowLeftOutlined,
  BookOutlined,
  CheckCircleOutlined,
  DownloadOutlined,
  FilePptOutlined,
  ReloadOutlined,
  RightOutlined,
  RobotOutlined,
  StarFilled,
  StarOutlined,
} from '@ant-design/icons'
import { bookmarkResource, getResource, updateResourceState } from '../api/resource'
import DocumentResourceViewer from '../components/DocumentResourceViewer'
import ExerciseResourceViewer from '../components/ExerciseResourceViewer'
import MindmapResourceViewer from '../components/MindmapResourceViewer'
import MarkdownRenderer from '../components/MarkdownRenderer'
import TextSelectionToolbar from '../components/TextSelectionToolbar'
import useTextSelection from '../hooks/useTextSelection'
import { useTutorContext } from '../contexts/TutorContext.jsx'
import {
  difficultyLabel,
  getResourceSourceLabel,
  getResourceStats,
  getTriggerReasonDescription,
  getTriggerReasonLabel,
  learningStatusLabel,
  normalizeTitle,
  typeLabel,
} from '../utils/resourceNormalizer'

const { Title, Text, Paragraph } = Typography

const RENDERERS = {
  document: DocumentResourceViewer,
  exercise: ExerciseResourceViewer,
  quiz: ExerciseResourceViewer,
  mindmap: MindmapResourceViewer,
}

export default function ResourceDetailPage() {
  const { resourceId } = useParams()
  const navigate = useNavigate()
  const [resource, setResource] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const contentRef = useRef(null)
  const { setTutorContext } = useTutorContext()
  const { selectedText, selectionRect, clearSelection } = useTextSelection(contentRef)

  // set tutor context for FloatingTutor
  useEffect(() => {
    if (!resource) return
    setTutorContext({
      courseId: resource.course_id,
      stageId: resource.stage_id,
      taskId: resource.task_id,
      courseTitle: resource.course_title || '',
      stageTitle: resource.stage_title || '',
      taskTitle: resource.task_title || resource.topic || '',
      topic: resource.topic || resource.title || '',
      learningGoal: '',
    })
    return () => setTutorContext({})
  }, [resource, setTutorContext])

  useEffect(() => {
    if (!resourceId) return
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError(null)
      getResource(resourceId)
        .then(setResource)
        .catch((err) => setError(err.message || '加载失败'))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [resourceId])

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300, background: '#F6F7FB' }}><Spin size="large" /></div>
  }
  if (error || !resource) {
    return (
      <div style={{ maxWidth: 500, margin: '60px auto', padding: 24 }}>
        <Result status="error" title="资源加载失败" subTitle={error || '资源不存在'}
          extra={<Button type="primary" icon={<ReloadOutlined />} onClick={() => window.location.reload()}>重试</Button>} />
      </div>
    )
  }

  const title = normalizeTitle(resource.title, resource.type, resource.topic)
  const Renderer = RENDERERS[resource.type]
  const stats = getResourceStats(resource)
  const label = typeLabel(resource.type)
  const diff = difficultyLabel(resource.difficulty)
  const stageTitle = resource.stage_title || (resource.stage_id ? `阶段 ${resource.stage_id}` : '')
  const taskRoute = resource.course_id && resource.task_id
    ? `/course/${resource.course_id}/learn/${resource.task_id}`
    : null
  const nextTaskRoute = resource.next_task?.route
    || (resource.course_id && resource.next_task?.task_id
      ? `/course/${resource.course_id}/learn/${resource.next_task.task_id}`
      : null)
  const state = resource.user_state || {}

  async function refreshResource() {
    const next = await getResource(resourceId)
    setResource(next)
  }

  async function toggleFavorite() {
    try {
      await bookmarkResource(resourceId)
      await refreshResource()
    } catch (err) {
      message.error(err.message || '收藏状态更新失败')
    }
  }

  async function markCompleted() {
    try {
      await updateResourceState(resourceId, { learning_status: 'completed' })
      await refreshResource()
      message.success('已标记为完成')
    } catch (err) {
      message.error(err.message || '学习状态更新失败')
    }
  }

  function askTutor() {
    // Open floating tutor instead of navigating away
    const prompt = `我想了解关于”${resource.topic || title}”的更多内容`
    window.__floatingTutorAsk?.(prompt)
  }

  return (
    <div style={{ minHeight: '100%', background: '#F6F7FB', padding: '20px 24px 48px' }}>
      <div style={{ maxWidth: 960, margin: '0 auto' }} ref={contentRef} data-tutor-content-area>
        <Space wrap style={{ marginBottom: 16 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(resource.course_id ? `/resources?courseId=${resource.course_id}` : '/resources')}
            style={{ paddingLeft: 0 }}
          >
            返回我的学习资料
          </Button>
          {taskRoute && <Button onClick={() => navigate(taskRoute)}>返回当前任务</Button>}
          {nextTaskRoute && <Button type="primary" onClick={() => navigate(nextTaskRoute)}>继续下一任务 <RightOutlined /></Button>}
          <Button icon={<RobotOutlined />} onClick={askTutor}>问 AI 学习助手</Button>
        </Space>

        {/* Header */}
        <div style={{ background: '#FFFFFF', borderRadius: 16, padding: '20px 28px', border: '1px solid #E5E7EB', marginBottom: 24 }}>
          <Space size={8} wrap style={{ marginBottom: 8 }}>
            <Tag color="purple" style={{ borderRadius: 6 }}>{label}</Tag>
            {diff && <Tag style={{ borderRadius: 6 }}>{diff}</Tag>}
            {stageTitle && <Tag style={{ borderRadius: 6, color: '#6B7280' }}>{stageTitle}</Tag>}
          </Space>
          <Title level={3} style={{ margin: '8px 0', color: '#111827' }}>{title}</Title>
          <Space size={16}>
            {stats && <Text style={{ fontSize: 13, color: '#6B7280' }}>{stats.icon} {stats.label}</Text>}
            {resource.topic && <Text style={{ fontSize: 13, color: '#6B7280' }}><BookOutlined /> {resource.topic}</Text>}
          </Space>
          <Descriptions size="small" column={{ xs: 1, sm: 3 }} style={{ marginTop: 16 }}>
            <Descriptions.Item label="所属课程">{resource.course_title || '未关联课程'}</Descriptions.Item>
            <Descriptions.Item label="所属阶段">{stageTitle || '未关联阶段'}</Descriptions.Item>
            <Descriptions.Item label="来源任务">{resource.task_title || resource.task_id || '自由生成'}</Descriptions.Item>
            <Descriptions.Item label="内容来源">{getResourceSourceLabel(resource)}</Descriptions.Item>
            <Descriptions.Item label="生成原因">{getTriggerReasonLabel(resource)}</Descriptions.Item>
            <Descriptions.Item label="学习状态">{learningStatusLabel(state.learning_status)}</Descriptions.Item>
          </Descriptions>
          <Space wrap style={{ marginTop: 14 }}>
            <Button
              icon={state.is_favorite ? <StarFilled style={{ color: '#F59E0B' }} /> : <StarOutlined />}
              onClick={toggleFavorite}
            >
              {state.is_favorite ? '取消收藏' : '收藏'}
            </Button>
            <Button
              icon={<CheckCircleOutlined />}
              disabled={state.learning_status === 'completed'}
              onClick={markCompleted}
            >
              {state.learning_status === 'completed' ? '已完成' : '标记完成'}
            </Button>
          </Space>
        </div>

        <Alert
          showIcon
          type="info"
          message="为什么为我生成"
          description={getTriggerReasonDescription(resource)}
          style={{ borderRadius: 12, marginBottom: 20, borderColor: '#DDD8FF', background: '#F3F0FF' }}
        />

        {/* Content area */}
        {Renderer ? (
          <Renderer resource={resource} />
        ) : resource.type === 'ppt' ? (
          <PptCard resource={resource} />
        ) : resource.type === 'interactive_classroom' ? (
          <ClassroomCard resource={resource} />
        ) : resource.type === 'code' ? (
          <CodeCard resource={resource} />
        ) : (
          <Card style={{ borderRadius: 14 }}>
            <MarkdownRenderer content={typeof resource.content === 'string' ? resource.content : JSON.stringify(resource.content, null, 2)} />
          </Card>
        )}

        {resource.related_resources?.length > 0 && (
          <Card title="相关讲义、导图和练习" style={{ borderRadius: 14, marginTop: 20 }}>
            <Space wrap>
              {resource.related_resources.map((item) => (
                <Button key={item.id} onClick={() => navigate(`/resources/${item.id}`)}>
                  {typeLabel(item.type)} · {item.title}
                </Button>
              ))}
            </Space>
          </Card>
        )}
      </div>
      <TextSelectionToolbar
        rect={selectionRect}
        visible={!!selectedText}
        onExplain={() => {
          window.__floatingTutorAsk?.(selectedText, '请详细解释下面这段话：')
          clearSelection()
        }}
        onAskAI={() => {
          window.__floatingTutorAsk?.(selectedText)
          clearSelection()
        }}
        onAddNote={() => {
          message.info('笔记功能开发中')
          clearSelection()
        }}
      />
    </div>
  )
}

/* ── PPT Card ── */

function PptCard({ resource }) {
  const content = typeof resource.content === 'string' ? (() => { try { return JSON.parse(resource.content) } catch { return resource.content } })() : (resource.content || {})
  const slides = content.slides || []
  const outline = content.outline || []
  const theme = content.theme || ''
  const fileName = content.file_name || ''
  const fileSize = content.file_size || 0

  // 格式化文件大小
  function formatSize(bytes) {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // 优先显示星火 PPT API 生成的结果
  if (outline.length > 0) {
    return (
      <Card title={<Space><FilePptOutlined style={{ color: '#FF6B6B' }} /><span>PPT 课件</span></Space>} style={{ borderRadius: 14 }}>
        <Descriptions column={1} size="small" style={{ marginBottom: 16 }}>
          <Descriptions.Item label="主题">{resource.topic || resource.title}</Descriptions.Item>
          <Descriptions.Item label="难度">{resource.difficulty || '中级'}</Descriptions.Item>
          {fileName && <Descriptions.Item label="文件名">{fileName}</Descriptions.Item>}
          {fileSize > 0 && <Descriptions.Item label="文件大小">{formatSize(fileSize)}</Descriptions.Item>}
          <Descriptions.Item label="章节数">{outline.length} 章</Descriptions.Item>
        </Descriptions>

        {/* 下载按钮 */}
        <div style={{ marginBottom: 20, textAlign: 'center' }}>
          {resource.artifact_url ? (
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              href={`/api/ppt/${resource.id}/download`}
              target="_blank"
              size="large"
              style={{ background: '#FF6B6B', borderColor: '#FF6B6B' }}
            >
              下载 PPT 文件
            </Button>
          ) : (
            <Button type="primary" icon={<DownloadOutlined />} disabled size="large">
              下载链接不可用
            </Button>
          )}
        </div>

        {/* 大纲预览 */}
        <Text strong style={{ display: 'block', marginBottom: 12 }}>📋 大纲预览</Text>
        <div style={{ maxHeight: 400, overflow: 'auto' }}>
          {outline.map((chapter, i) => (
            <Card key={i} size="small" style={{ marginBottom: 8, borderRadius: 10, border: '1px solid #E5E7EB' }}
              title={<Text strong style={{ fontSize: 14 }}>{i + 1}. {chapter.title}</Text>}>
              {chapter.subtitles?.map((sub, j) => (
                <div key={j} style={{ marginBottom: 8 }}>
                  <Text strong style={{ fontSize: 13, display: 'block' }}>{sub.title}</Text>
                  {sub.content && <Text type="secondary" style={{ fontSize: 12 }}>{sub.content}</Text>}
                </div>
              ))}
            </Card>
          ))}
        </div>
      </Card>
    )
  }

  // 兼容旧格式
  return (
    <Card title={`${theme ? theme + ' · ' : ''}${slides.length} 张幻灯片`} style={{ borderRadius: 14 }}>
      {resource.artifact_url ? (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <Button type="primary" href={resource.artifact_url} target="_blank">下载 PPT 文件</Button>
        </div>
      ) : (
        <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>PPT 内容方案（尚未生成 .pptx 文件）</Text>
      )}
      {slides.map((s, i) => (
        <Card key={i} size="small" style={{ marginBottom: 8, borderRadius: 10, border: '1px solid #E5E7EB' }}
          title={`第 ${s.slide_number || i + 1} 页 · ${s.title || ''}`}>
          {s.elements?.map((el, j) => (
            <Paragraph key={j} style={{ margin: 0, color: '#374151' }}>{el.content || ''}</Paragraph>
          ))}
          {s.speaker_notes && <Text type="secondary" style={{ fontSize: 12 }}>备注: {s.speaker_notes}</Text>}
        </Card>
      ))}
      {slides.length === 0 && <Empty description="暂无幻灯片内容" />}
    </Card>
  )
}

/* ── Classroom Card ── */

function ClassroomCard({ resource }) {
  const content = typeof resource.content === 'string' ? (() => { try { return JSON.parse(resource.content) } catch { return {} } })() : (resource.content || {})
  const scenes = content.scenes || []
  return (
    <Card title="AI 互动课堂" style={{ borderRadius: 14 }}>
      <Descriptions column={1} size="small" style={{ marginBottom: 16 }}>
        <Descriptions.Item label="课堂标题">{resource.title}</Descriptions.Item>
        <Descriptions.Item label="场景数">{scenes.length} 个</Descriptions.Item>
        <Descriptions.Item label="预计时长">{content.estimated_minutes || resource.estimated_minutes || 25} 分钟</Descriptions.Item>
        <Descriptions.Item label="难度">{difficultyLabel(resource.difficulty)}</Descriptions.Item>
      </Descriptions>
      {scenes.map((s, i) => (
        <Tag key={i} color="purple" style={{ margin: 4, borderRadius: 8 }}>{s.title || `场景 ${i + 1}`}</Tag>
      ))}
      {scenes.length === 0 && <Empty description="暂无课堂场景数据" />}
    </Card>
  )
}

/* ── Code Card（支持实验模式） ── */

const EXPERIMENT_MODE_LABELS = {
  code_guide: '📖 代码导读',
  param_experiment: '🔬 参数实验',
  code_completion: '✏️ 代码补全',
  error_diagnosis: '🐛 错误诊断',
  mini_project: '🚀 小型项目',
}

function CodeCard({ resource }) {
  const navigate = useNavigate()
  const content = typeof resource.content === 'string' ? (() => { try { return JSON.parse(resource.content) } catch { return resource.content } })() : (resource.content || {})
  const isExperiment = !!content.experiment_mode
  const code = content.starter_code || content.code || content.snippet || ''

  const handleOpenExperiment = () => {
    // 将实验数据存入 localStorage，供实验页面读取
    localStorage.setItem('current_experiment', JSON.stringify({
      ...content,
      title: resource.title || content.title,
    }))
    navigate(`/code-experiment/${resource.id}`)
  }

  return (
    <Card
      title={
        <Space>
          {isExperiment ? '交互式代码实验' : '代码案例'}
          {isExperiment && (
            <Tag color="blue">
              {EXPERIMENT_MODE_LABELS[content.experiment_mode] || content.experiment_mode}
            </Tag>
          )}
        </Space>
      }
      style={{ borderRadius: 14 }}
      extra={isExperiment && (
        <Button type="primary" onClick={handleOpenExperiment}>
          🚀 进入实验
        </Button>
      )}
    >
      {/* 实验概览信息 */}
      {isExperiment && (
        <div style={{ marginBottom: 16 }}>
          {content.scenario && (
            <Paragraph style={{ color: '#374151', marginBottom: 12 }}>{content.scenario}</Paragraph>
          )}
          <Space size={8} wrap>
            <Tag>难度：{content.difficulty || '中级'}</Tag>
            <Tag>预计 {content.estimated_minutes || 30} 分钟</Tag>
            {content.steps?.length > 0 && <Tag>{content.steps.length} 个步骤</Tag>}
            {content.editable_parameters?.length > 0 && <Tag>{content.editable_parameters.length} 个可调参数</Tag>}
          </Space>

          {content.learning_objectives?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <Text strong style={{ fontSize: 13 }}>学习目标：</Text>
              <ul style={{ margin: '4px 0 0', paddingLeft: 20 }}>
                {content.learning_objectives.map((obj, i) => (
                  <li key={i} style={{ fontSize: 13, color: '#555' }}>{obj}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* 代码预览 */}
      {content.explanation && !isExperiment && (
        <Paragraph style={{ color: '#374151', marginBottom: 16 }}>{content.explanation}</Paragraph>
      )}
      {code ? (
        <pre style={{
          background: '#1E1E2E', color: '#CDD6F4', padding: 20,
          borderRadius: 12, overflow: 'auto', fontSize: 13, lineHeight: 1.6,
          maxHeight: isExperiment ? 300 : undefined,
        }}>
          <code>{code}</code>
        </pre>
      ) : (
        <Empty description="暂无代码内容" />
      )}

      {/* 实验模式：展示步骤概览 */}
      {isExperiment && content.steps?.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>实验步骤：</Text>
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            {content.steps.map((step, i) => (
              <li key={i} style={{ fontSize: 13, color: '#555', marginBottom: 4 }}>
                <Text strong>{step.title}</Text>
                {step.instruction && <Text type="secondary"> — {step.instruction.slice(0, 50)}...</Text>}
              </li>
            ))}
          </ol>
        </div>
      )}
    </Card>
  )
}
