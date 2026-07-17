import { Card, Progress, Typography } from 'antd'

const { Text } = Typography

export default function PptResultCard({ task }) {
  if (!task) return null
  return (
    <Card className="workspace-tool-card">
      <Text strong>PPT 生成进度</Text>
      <Progress percent={task.progress || 0} strokeColor="#20C7B7" />
      <Text type="secondary">{task.message || '等待生成结果'}</Text>
    </Card>
  )
}
