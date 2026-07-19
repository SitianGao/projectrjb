import { Alert, Button, Card, Progress, Space } from 'antd'
import { ArrowRightOutlined, FileTextOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

export default function ResourceResultCard({ task }) {
  const navigate = useNavigate()
  if (!task) return null
  const result = task.result || {}
  const resource = result.resource
  return (
    <Card className="workspace-tool-card">
      <Alert
        type={task.status === 'failed' ? 'error' : task.status === 'done' ? 'success' : 'info'}
        showIcon
        message={task.message || '资源任务已创建'}
        description={task.error?.message}
      />
      <Progress percent={task.progress || 0} strokeColor="#6C5CE7" />
      {task.status === 'done' && (
        <Space wrap>
          {resource?.id && (
            <Button icon={<FileTextOutlined />} onClick={() => navigate(`/resources/${resource.id}`)}>
              查看资源
            </Button>
          )}
          {result.learning_route && (
            <Button type="primary" icon={<ArrowRightOutlined />} onClick={() => navigate(result.learning_route)}>
              进入学习任务
            </Button>
          )}
        </Space>
      )}
    </Card>
  )
}
