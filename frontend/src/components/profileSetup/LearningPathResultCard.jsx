import { Button, Card, Space, Tag, Typography } from 'antd'
import { BranchesOutlined, PlayCircleOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

export default function LearningPathResultCard({ result, onEnterCourse, onViewPath }) {
  if (!result?.path) return null
  const stages = result.path.stages || []
  return (
    <Card className="learning-path-result-card">
      <Tag color="purple">生成完成</Tag>
      <Title level={4}>学习路径已准备好</Title>
      <Text type="secondary">共 {stages.length} 个阶段。你可以先查看完整路径，也可以进入当前任务。</Text>
      <div className="result-stage-list">
        {stages.slice(0, 4).map((stage) => (
          <span key={stage.stage_id}>{stage.title}</span>
        ))}
      </div>
      <Space wrap>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={onEnterCourse}>进入当前任务</Button>
        <Button icon={<BranchesOutlined />} onClick={onViewPath}>查看完整学习路径</Button>
      </Space>
    </Card>
  )
}
