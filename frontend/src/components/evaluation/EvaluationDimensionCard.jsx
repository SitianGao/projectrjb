import { Card, Progress, Typography } from 'antd'

const { Text } = Typography

export default function EvaluationDimensionCard({ item }) {
  const rawScore = item?.score
  const hasScore = rawScore !== null && rawScore !== undefined && rawScore >= 0
  const score = hasScore ? Number(rawScore) : null
  const delta = item?.delta
  return (
    <Card className="evaluation-card dimension-card">
      <Text>{item?.label}</Text>
      <strong>{hasScore ? `${score}%` : '—'}</strong>
      {delta != null && <span className={delta >= 0 ? 'delta-up' : 'delta-down'}>{delta >= 0 ? `+${delta}` : delta}%</span>}
      {hasScore ? (
        <Progress percent={score} showInfo={false} strokeColor="#6C5CE7" trailColor="#F3F0FF" />
      ) : (
        <Text type="secondary">暂无数据</Text>
      )}
      <p>{item?.comment}</p>
    </Card>
  )
}
