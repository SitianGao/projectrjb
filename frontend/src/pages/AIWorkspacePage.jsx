import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import ConversationSidebar from '../components/aiWorkspace/ConversationSidebar'
import WorkspaceContextBar from '../components/aiWorkspace/WorkspaceContextBar'
import WorkspaceChatPanel from '../components/aiWorkspace/WorkspaceChatPanel'
import WorkspaceRightPanel from '../components/aiWorkspace/WorkspaceRightPanel'
import { createResourceJob, createTutorResource, getTaskStatus } from '../services/aiWorkspaceService'
import { getCourseDashboard } from '../api/courses'
import { useAIWorkspace } from '../hooks/useAIWorkspace'
import './AIWorkspacePage.css'

export default function AIWorkspacePage() {
  const navigate = useNavigate()
  const workspace = useAIWorkspace()
  const [generating, setGenerating] = useState(false)
  const [resourceTasks, setResourceTasks] = useState([])
  const [dashboard, setDashboard] = useState(null)

  // ── load course context (current task, stage, weak points, recent resources) ──
  useEffect(() => {
    if (!workspace.courseId) return
    getCourseDashboard(workspace.courseId)
      .then(setDashboard)
      .catch(() => setDashboard(null))
  }, [workspace.courseId])

  const currentStage = dashboard?.current_stage
  const currentTask = dashboard?.current_task
  const weakPoints = dashboard?.weak_points || []
  const recentResources = dashboard?.recommended_resources || []

  const welcomeMessage = currentTask?.title
    ? `你正在学习「${currentTask.title}」。${
        weakPoints.length > 0
          ? `根据最近学习记录，你对「${typeof weakPoints[0] === 'string' ? weakPoints[0] : weakPoints[0]?.name || '相关知识点'}」的掌握相对较弱。`
          : ''
      }我可以为你讲解核心概念，也可以陪你完成代码实践。`
    : null

  // ── resource generation ──
  const pollTask = async (taskId, updateFn) => {
    for (let i = 0; i < 20; i += 1) {
      const status = await getTaskStatus(taskId)
      updateFn(status)
      if (status.status === 'done' || status.status === 'failed') return status
      await new Promise((r) => setTimeout(r, 1200))
    }
    return null
  }

  const generate = async (types) => {
    if (!workspace.studentId) return
    setGenerating(true)
    try {
      const task = await createResourceJob({
        student_id: workspace.studentId,
        topic: currentTask?.title || workspace.course?.title || '当前课程',
        types,
        difficulty: currentTask?.difficulty || '中级',
        count: 1,
      })
      const entry = { ...task, status: 'started', progress: 0 }
      setResourceTasks((prev) => [entry, ...prev.slice(0, 9)])
      pollTask(task.task_id, (st) => {
        setResourceTasks((prev) => prev.map((t) =>
          t.task_id === task.task_id ? { ...t, ...st, progress: st.progress || 50 } : t))
      }).catch(() => {})
    } catch (err) {
      message.error(err.message || '生成任务创建失败')
    } finally {
      setGenerating(false)
    }
  }

  const convertConversation = async (content, resourceType) => {
    if (!workspace.courseId) { message.warning('请先选择课程'); return }
    setGenerating(true)
    try {
      const task = await createTutorResource({
        course_id: workspace.courseId,
        session_id: workspace.sessionId,
        message: content.slice(0, 500),
        topic: workspace.course?.title || '当前对话主题',
        action: resourceType,
        resource_type: resourceType,
      })
      const entry = { ...task, status: 'started', progress: 0 }
      setResourceTasks((prev) => [entry, ...prev.slice(0, 9)])
      pollTask(task.task_id, (st) => {
        setResourceTasks((prev) => prev.map((t) =>
          t.task_id === task.task_id ? { ...t, ...st, progress: st.progress || 50 } : t))
      }).catch(() => {})
    } catch (err) {
      message.error(err.message || '对话转资源失败')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="ai-workspace-page">
      <div className="ai-workspace-container">
        {/* ── Compact context bar ── */}
        <WorkspaceContextBar
          course={workspace.course}
          currentStage={currentStage}
          currentTask={currentTask}
          onViewTask={() => {
            if (currentTask?.task_id) {
              navigate(`/course/${workspace.courseId}/learn/${encodeURIComponent(currentTask.task_id)}`)
            }
          }}
        />

        {/* ── 3-column layout ── */}
        <div className="ai-workspace-layout">
          <ConversationSidebar />
          <WorkspaceChatPanel
            messages={workspace.messages}
            loading={workspace.loading}
            onSend={workspace.send}
            onConvert={convertConversation}
            converting={generating}
            currentTask={currentTask}
            welcomeMessage={welcomeMessage}
          />
          <WorkspaceRightPanel
            currentTask={currentTask}
            weakPoints={weakPoints}
            recentResources={recentResources.length > 0 ? recentResources : resourceTasks}
            onGenerate={generate}
            onResourceClick={(r) => {
              if (r.id) navigate(`/resources/${r.id}`)
              else if (r.task_id) {
                const entry = resourceTasks.find((t) => t.task_id === r.task_id)
                if (entry?.result?.resource?.id) navigate(`/resources/${entry.result.resource.id}`)
              }
            }}
            generating={generating}
          />
        </div>
      </div>
    </div>
  )
}
