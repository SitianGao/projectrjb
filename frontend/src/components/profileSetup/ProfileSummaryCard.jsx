import { Card, Descriptions } from 'antd'

export default function ProfileSummaryCard({ summary }) {
  return (
    <Card className="profile-summary-card" title="画像摘要">
      <Descriptions size="small" column={1}>
        <Descriptions.Item label="学习目标">{summary.goal}</Descriptions.Item>
        <Descriptions.Item label="基础水平">{summary.level}</Descriptions.Item>
        <Descriptions.Item label="学习节奏">{summary.pace}</Descriptions.Item>
      </Descriptions>
    </Card>
  )
}
