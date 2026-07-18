import { Button, Card, Space, Tag, Typography } from 'antd'
import { ExperimentOutlined, PlayCircleOutlined, ThunderboltOutlined } from '@ant-design/icons'

const { Text, Paragraph } = Typography

export default function ClassroomResourceCard({ title, description, onEnter, onGenerate, generating }) {
  return (
    <Card className="classroom-resource-card">
      <div className="classroom-resource-icon"><ExperimentOutlined /></div>
      <div className="classroom-resource-main">
        <Space size={6}>
          <Tag color="purple">OpenMAIC</Tag>
          <Tag color="cyan">互动课堂</Tag>
        </Space>
        <Text strong>{title || '梯度下降与学习率沉浸式课堂'}</Text>
        <Paragraph>{description || '把讲义、模拟实验、课堂提问和阶段测评合并为一个学习任务。'}</Paragraph>
      </div>
      <Space>
        <Button icon={<ThunderboltOutlined />} loading={generating} onClick={onGenerate}>重新生成</Button>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={onEnter}>进入课堂</Button>
      </Space>
    </Card>
  )
}
