import { Card, Progress, Typography } from 'antd'

const { Text } = Typography

export default function EvaluationDimensionCard({ item }) {
  const score = Number(item?.score || 0)
  const delta = item?.delta
  return (
    <Card className="evaluation-card dimension-card">
      <Text>{item?.label}</Text>
      <strong>{score}%</strong>
      {delta != null && <span className={delta >= 0 ? 'delta-up' : 'delta-down'}>{delta >= 0 ? `+${delta}` : delta}%</span>}
      <Progress percent={score} showInfo={false} strokeColor="#6C5CE7" trailColor="#F3F0FF" />
      <p>{item?.comment}</p>
    </Card>
  )
}
