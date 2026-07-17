import { Button, Card, Progress, Space, Tag, Typography } from 'antd'

const { Text } = Typography

export default function WeakKnowledgeCard({ item, onEvidence, onAction }) {
  return (
    <Card className="knowledge-card weak-card" size="small">
      <div className="knowledge-card-head">
        <Text strong>{item.name}</Text>
        <Tag color={item.priority === 'high' ? 'red' : 'orange'}>{item.priority === 'high' ? '高优先级' : '中优先级'}</Tag>
      </div>
      <div className="weak-score">
        <Progress percent={item.score} showInfo={false} strokeColor="#EF4444" />
        <strong>{item.score}%</strong>
      </div>
      <p>{item.reason}</p>
      <Text type="secondary">证据数量：{item.evidence_count || item.evidence?.length || 0}</Text>
      <Space wrap>
        {(item.actions || []).slice(0, 3).map((action) => (
          <Button key={action.type} size="small" onClick={() => onAction?.(action, item)}>
            {action.title}
          </Button>
        ))}
        <Button size="small" type="link" onClick={() => onEvidence?.(item)}>查看依据</Button>
      </Space>
    </Card>
  )
}
