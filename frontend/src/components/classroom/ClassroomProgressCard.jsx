import { Card, Progress, Space, Statistic } from 'antd'
import { ClockCircleOutlined, CommentOutlined, TrophyOutlined } from '@ant-design/icons'

export default function ClassroomProgressCard({ progress, session }) {
  return (
    <Card className="classroom-progress-card">
      <Progress percent={progress.percent} strokeColor="#6C5CE7" />
      <Space size={16} wrap>
        <Statistic title="已完成场景" value={`${progress.completed}/${progress.total}`} prefix={<TrophyOutlined />} />
        <Statistic title="学习时长" value={session?.duration_minutes || 0} suffix="分钟" prefix={<ClockCircleOutlined />} />
        <Statistic title="导师问答" value={session?.tutor_question_count || 0} prefix={<CommentOutlined />} />
      </Space>
    </Card>
  )
}
