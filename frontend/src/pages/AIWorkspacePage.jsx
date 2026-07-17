import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import ConversationSidebar from '../components/aiWorkspace/ConversationSidebar'
import WorkspaceContextBar from '../components/aiWorkspace/WorkspaceContextBar'
import WorkspaceChatPanel from '../components/aiWorkspace/WorkspaceChatPanel'
import ResourceGenerationCard from '../components/aiWorkspace/ResourceGenerationCard'
import ResourceResultCard from '../components/aiWorkspace/ResourceResultCard'
import PptGenerationCard from '../components/aiWorkspace/PptGenerationCard'
import PptResultCard from '../components/aiWorkspace/PptResultCard'
import { createResourceJob, getTaskStatus } from '../services/aiWorkspaceService'
import { useAIWorkspace } from '../hooks/useAIWorkspace'
import './AIWorkspacePage.css'

export default function AIWorkspacePage() {
  const navigate = useNavigate()
  const workspace = useAIWorkspace()
  const [resourceTask, setResourceTask] = useState(null)
  const [pptTask, setPptTask] = useState(null)
  const [generating, setGenerating] = useState(false)

  const pollTask = async (taskId, setter) => {
    for (let i = 0; i < 20; i += 1) {
      const status = await getTaskStatus(taskId)
      setter(status)
      if (status.status === 'done' || status.status === 'failed') return status
      await new Promise((resolve) => setTimeout(resolve, 1200))
    }
    return null
  }

  const generate = async (types) => {
    if (!workspace.studentId) return
    setGenerating(true)
    try {
      const task = await createResourceJob({
        student_id: workspace.studentId,
        topic: workspace.course?.title || '当前课程',
        types,
        difficulty: '中级',
        count: 1,
      })
      if (types.includes('ppt')) setPptTask(task)
      else setResourceTask(task)
      const setter = types.includes('ppt') ? setPptTask : setResourceTask
      pollTask(task.task_id, setter).catch(() => {})
    } catch (err) {
      message.error(err.message || '生成任务创建失败')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="ai-workspace-page">
      <div className="ai-workspace-container">
        <WorkspaceContextBar
          course={workspace.course}
          onPath={() => navigate(workspace.courseId ? `/course/${workspace.courseId}/path` : '/courses')}
          onEvaluate={() => navigate(workspace.courseId ? `/course/${workspace.courseId}/assessment/report` : '/assessment/tests')}
          onResources={() => navigate(workspace.courseId ? `/resources?courseId=${workspace.courseId}` : '/resources')}
        />
        <div className="ai-workspace-layout">
          <ConversationSidebar />
          <WorkspaceChatPanel messages={workspace.messages} loading={workspace.loading} onSend={workspace.send} />
          <div className="workspace-tool-stack">
            <ResourceGenerationCard loading={generating} onGenerate={generate} />
            <ResourceResultCard task={resourceTask} />
            <PptGenerationCard loading={generating} onGenerate={generate} />
            <PptResultCard task={pptTask} />
          </div>
        </div>
      </div>
    </div>
  )
}
