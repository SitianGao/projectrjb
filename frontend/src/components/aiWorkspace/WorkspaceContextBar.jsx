import { Button, Card, Space, Tag, Typography } from 'antd'
import { BranchesOutlined, CheckCircleOutlined, FileTextOutlined } from '@ant-design/icons'

const { Text } = Typography

export default function WorkspaceContextBar({ course, onPath, onEvaluate, onResources }) {
  return (
    <Card className="workspace-context-bar">
      <div>
        <Tag color="purple">AI 学习工作台</Tag>
        <Text strong>{course?.title || '当前课程'}</Text>
        <Text type="secondary">围绕当前课程画像、路径和任务进行答疑、资源生成与评估。</Text>
      </div>
      <Space wrap>
        <Button icon={<BranchesOutlined />} onClick={onPath}>学习路径</Button>
        <Button icon={<FileTextOutlined />} onClick={onResources}>资源中心</Button>
        <Button icon={<CheckCircleOutlined />} onClick={onEvaluate}>学习评估</Button>
      </Space>
    </Card>
  )
}
