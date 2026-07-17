import { Alert, Card, Progress } from 'antd'

export default function ResourceResultCard({ task }) {
  if (!task) return null
  return (
    <Card className="workspace-tool-card">
      <Alert type={task.status === 'failed' ? 'error' : 'info'} showIcon message={task.message || '资源任务已创建'} />
      <Progress percent={task.progress || 0} strokeColor="#6C5CE7" />
    </Card>
  )
}
