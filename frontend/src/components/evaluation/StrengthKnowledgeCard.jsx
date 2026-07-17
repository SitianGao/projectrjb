import { Card, Progress, Typography } from 'antd'

const { Text } = Typography

export default function StrengthKnowledgeCard({ item }) {
  return (
    <Card className="knowledge-card strength-card" size="small">
      <div className="knowledge-card-head">
        <Text strong>{item.name}</Text>
        <strong>{item.score}%</strong>
      </div>
      <Progress percent={item.score} showInfo={false} strokeColor="#22C55E" />
      <p>{item.reason}</p>
    </Card>
  )
}
