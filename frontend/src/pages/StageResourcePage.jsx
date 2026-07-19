import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Alert,
  Breadcrumb,
  Button,
  Card,
  Empty,
  Result,
  Skeleton,
  Space,
  Steps,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  ArrowLeftOutlined,
  BookOutlined,
  BranchesOutlined,
  CheckCircleOutlined,
  CodeOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  HomeOutlined,
  ReadOutlined,
  ReloadOutlined,
  RightOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { completeCourseTask, getCourseLearningPath } from '../api/courseLearning'
import {
  generateTaskResource,
  getTaskResource,
} from '../api/resource'
import DocumentResourceViewer from '../components/DocumentResourceViewer'
import ExerciseResourceViewer from '../components/ExerciseResourceViewer'
import MindmapResourceViewer from '../components/MindmapResourceViewer'
import MarkdownRenderer from '../components/MarkdownRenderer'
import TextSelectionToolbar from '../components/TextSelectionToolbar'
import useTextSelection from '../hooks/useTextSelection'
import { useTutorContext } from '../contexts/TutorContext.jsx'
import './StageResourcePage.css'

const { Paragraph, Text, Title } = Typography

const GENERATION_STEPS = [
  '正在分析当前学习任务',
  '正在检索课程知识库',
  '正在结合你的学习情况生成内容',
  '正在检查内容质量',
]

const TYPE_LABELS = {
  document: '核心讲义',
  exercise: '针对性练习',
  code: '代码示例',
  mindmap: '知识导图',
  reading: '拓展阅读',
  ppt: '教学课件',
  interactive_classroom: 'AI 互动课堂',
}

const VARIANT_ACTIONS = [
  { key: 'alternative_explanation', label: '换一种方式讲解', icon: <SyncOutlined /> },
  { key: 'basic', label: '生成基础版', difficulty: '初级', icon: <ReadOutlined /> },
  { key: 'advanced', label: '生成进阶版', difficulty: '高级', icon: <BookOutlined /> },
  { key: 'life_case', label: '补充生活化案例', icon: <ExperimentOutlined /> },
  { key: 'code_example', label: '生成代码示例', resourceType: 'code', icon: <CodeOutlined /> },
  { key: 'mindmap', label: '生成知识导图', resourceType: 'mindmap', icon: <BranchesOutlined /> },
  { key: 'practice', label: '针对此内容练习', resourceType: 'exercise', icon: <CheckCircleOutlined /> },
]

export default function StageResourcePage() {
  const { courseId, taskId, stageId } = useParams()
  const navigate = useNavigate()
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [generationStep, setGenerationStep] = useState(0)
  const [error, setError] = useState(null)

  const pathUrl = courseId ? `/course/${courseId}/path` : '/courses'
  const contentRef = useRef(null)
  const { setTutorContext } = useTutorContext()
  const { selectedText, selectionRect, clearSelection } = useTextSelection(contentRef)

  const prepareResource = useCallback(async (options = {}) => {
    if (!courseId || !taskId) return
    setGenerating(true)
    setError(null)
    setGenerationStep(0)
    const timer = window.setInterval(() => {
      setGenerationStep((current) => Math.min(current + 1, GENERATION_STEPS.length - 1))
    }, 900)
    try {
      const result = await generateTaskResource(courseId, taskId, {
        trigger_source: 'learning_task',
        trigger_context: { route: `/course/${courseId}/learn/${taskId}` },
        ...options,
      })
      setPayload(result)
      if (result?.fallback_type === 'knowledge_base_basic') {
        message.warning('已使用课程知识库基础版本')
      } else if (result?.fallback_type === 'outline') {
        message.warning('已创建可继续学习的内容提纲')
      }
    } catch (err) {
      setError(err.message || '学习内容准备失败')
    } finally {
      window.clearInterval(timer)
      setGenerating(false)
    }
  }, [courseId, taskId])

  const pollGeneratingResource = useCallback(async () => {
    setGenerating(true)
    setGenerationStep(0)
    for (let index = 0; index < 30; index += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 1500))
      const result = await getTaskResource(courseId, taskId)
      setGenerationStep(Math.min(Math.floor(index / 2), GENERATION_STEPS.length - 1))
      if (result?.status === 'ready') {
        setPayload(result)
        setGenerating(false)
        return
      }
      if (result?.status === 'missing') {
        setGenerating(false)
        await prepareResource()
        return
      }
    }
    setGenerating(false)
    setError('学习内容准备时间较长，请稍后重新加载')
  }, [courseId, prepareResource, taskId])

  const loadTask = useCallback(async () => {
    if (!courseId || !taskId) return
    setLoading(true)
    setError(null)
    try {
      const result = await getTaskResource(courseId, taskId)
      setPayload(result)
      if (result?.status === 'missing') {
        await prepareResource()
      } else if (result?.status === 'generating' || result?.status === 'pending') {
        await pollGeneratingResource()
      }
    } catch (err) {
      setError(err.message || '当前学习任务加载失败')
    } finally {
      setLoading(false)
    }
  }, [courseId, pollGeneratingResource, prepareResource, taskId])

  useEffect(() => {
    if (!stageId || taskId || !courseId) return
    let cancelled = false
    getCourseLearningPath(courseId)
      .then((result) => {
        if (cancelled) return
        const path = result?.path || result
        const stage = path?.stages?.find((item) => String(item.stage_id) === String(stageId))
        const task = stage?.tasks?.find((item) => !['completed', 'locked'].includes(item.status))
          || stage?.tasks?.find((item) => item.status !== 'locked')
        if (task?.task_id) {
          navigate(`/course/${courseId}/learn/${encodeURIComponent(task.task_id)}`, { replace: true })
        } else {
          navigate(pathUrl, { replace: true })
        }
      })
      .catch(() => navigate(pathUrl, { replace: true }))
    return () => { cancelled = true }
  }, [courseId, navigate, pathUrl, stageId, taskId])

  useEffect(() => {
    if (!taskId) return undefined
    const timer = window.setTimeout(() => loadTask(), 0)
    return () => window.clearTimeout(timer)
  }, [loadTask, taskId])

  // set tutor context for FloatingTutor
  useEffect(() => {
    if (!payload) return
    const ctx = payload.context || {}
    const res = payload.resource
    setTutorContext({
      courseId,
      stageId: stageId || ctx.stage?.stage_id,
      taskId,
      courseTitle: ctx.course?.title || '',
      stageTitle: ctx.stage?.title || '',
      taskTitle: ctx.task?.title || res?.title || '',
      topic: ctx.task?.title || res?.topic || res?.title || '',
      learningGoal: ctx.course?.goal || '',
    })
    return () => setTutorContext({})
  }, [payload, courseId, stageId, taskId, setTutorContext])

  const context = payload?.context || {}
  const task = context.task || {}
  const stage = context.stage || {}
  const course = context.course || {}
  const resource = payload?.resource

  const fallbackAlert = useMemo(() => {
    if (payload?.fallback_type === 'knowledge_base_basic') {
      return 'AI 生成暂时不可用，已根据课程知识库准备基础版本。'
    }
    if (payload?.fallback_type === 'outline') {
      return '暂时无法生成完整内容，已为你创建学习提纲。'
    }
    return null
  }, [payload?.fallback_type])

  const generateVariant = async (action) => {
    if (!resource?.id) return
    await prepareResource({
      resource_type: action.resourceType || resource.type,
      difficulty: action.difficulty || resource.difficulty,
      parent_resource_id: resource.id,
      variant_type: action.key,
      force_regenerate: true,
    })
  }

  const completeAndContinue = async () => {
    try {
      const result = await completeCourseTask(courseId, taskId)
      message.success('任务已完成，学习进度已更新')
      const nextRoute = result?.next_task?.task_id
        ? `/course/${courseId}/learn/${result.next_task.task_id}`
        : payload?.next_task?.route
      navigate(nextRoute || pathUrl)
    } catch (err) {
      message.error(err.message || '保存学习进度失败')
    }
  }

  if (stageId && !taskId) {
    return <div className="task-resource-state"><Skeleton active paragraph={{ rows: 5 }} /></div>
  }

  if (loading && !payload) {
    return <div className="task-resource-state"><Skeleton active paragraph={{ rows: 8 }} /></div>
  }

  if (error && !resource && !generating) {
    return (
      <div className="task-resource-state">
        <Result
          status="error"
          title="当前学习内容加载失败"
          subTitle={error}
          extra={[
            <Button key="back" onClick={() => navigate(pathUrl)}>返回学习路径</Button>,
            <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={loadTask}>重新加载</Button>,
          ]}
        />
      </div>
    )
  }

  return (
    <div className="task-resource-page">
      <div className="task-resource-container">
        <Breadcrumb
          className="task-resource-breadcrumb"
          items={[
            { title: <span onClick={() => navigate('/home')}><HomeOutlined /> 学习首页</span> },
            { title: <span onClick={() => navigate(pathUrl)}>{course.title || '学习路径'}</span> },
            { title: stage.title || '当前阶段' },
            { title: task.title || '当前任务' },
          ]}
        />

        <Card className="task-context-card">
          <div className="task-context-main">
            <Space size={8} wrap>
              <Tag color="purple">{TYPE_LABELS[resource?.type || task.task_type] || '学习任务'}</Tag>
              {task.difficulty && <Tag>{task.difficulty}</Tag>}
              {task.estimated_minutes && <Tag>{task.estimated_minutes} 分钟</Tag>}
            </Space>
            <Title level={3}>{task.title || resource?.title || '当前学习任务'}</Title>
            <Paragraph>{task.description || stage.title || '按学习路径完成本次学习内容。'}</Paragraph>
          </div>
          <Space wrap>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(pathUrl)}>返回学习路径</Button>
            <Button onClick={() => navigate('/resources')}>我的学习资料</Button>
          </Space>
        </Card>

        {generating ? (
          <Card className="generation-card">
            <Title level={4}>正在为你准备本次学习内容</Title>
            <Steps
              direction="vertical"
              current={generationStep}
              items={GENERATION_STEPS.map((title, index) => ({
                title,
                status: index < generationStep ? 'finish' : index === generationStep ? 'process' : 'wait',
              }))}
            />
          </Card>
        ) : resource ? (
          <>
            {fallbackAlert && (
              <Alert
                className="task-resource-alert"
                type="warning"
                showIcon
                message={fallbackAlert}
                action={
                  <Button
                    size="small"
                    type="primary"
                    loading={generating}
                    onClick={() => prepareResource({
                      force_regenerate: true,
                      generation_version: '2',
                      trigger_source: 'learning_task',
                      trigger_context: { route: location.pathname, reason: 'retry_degraded_resource' },
                    })}
                  >
                    重新生成个性化版本
                  </Button>
                }
              />
            )}
            <Card className="learning-resource-card" ref={contentRef} data-tutor-content-area>
              <div className="resource-heading">
                <div>
                  <Text type="secondary">当前学习内容</Text>
                  <Title level={3}>{resource.title}</Title>
                </div>
                {payload?.reused && <Tag color="green">已复用已有资料</Tag>}
              </div>
              <ResourceContent resource={resource} />
            </Card>

            <Card className="variant-card" title="需要更适合你的版本？">
              <Space wrap>
                {VARIANT_ACTIONS.map((action) => (
                  <Button
                    key={action.key}
                    icon={action.icon}
                    onClick={() => generateVariant(action)}
                  >
                    {action.label}
                  </Button>
                ))}
              </Space>
            </Card>

            {payload?.related_resources?.length > 1 && (
              <Card className="related-card" title="本任务相关资料">
                <Space wrap>
                  {payload.related_resources
                    .filter((item) => item.id !== resource.id)
                    .map((item) => (
                      <Button
                        key={item.id}
                        icon={<FileTextOutlined />}
                        onClick={() => navigate(`/resources/${item.id}`)}
                      >
                        {item.title}
                      </Button>
                    ))}
                </Space>
              </Card>
            )}

            <div className="task-resource-actions">
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(pathUrl)}>查看完整学习路径</Button>
              <Button type="primary" icon={<CheckCircleOutlined />} onClick={completeAndContinue}>
                完成并进入下一任务 <RightOutlined />
              </Button>
            </div>
          </>
        ) : (
          <Card className="generation-card">
            <Empty description="本任务还没有学习内容">
              <Button type="primary" onClick={() => prepareResource()}>
                为我准备本次学习内容
              </Button>
            </Empty>
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

function ResourceContent({ resource }) {
  if (resource.type === 'document') return <DocumentResourceViewer resource={resource} />
  if (resource.type === 'exercise') return <ExerciseResourceViewer resource={resource} />
  if (resource.type === 'mindmap') return <MindmapResourceViewer resource={resource} />
  const content = typeof resource.content === 'string'
    ? resource.content
    : JSON.stringify(resource.content || {}, null, 2)
  return <MarkdownRenderer content={content} />
}
