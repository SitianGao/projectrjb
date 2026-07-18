import { Card, Typography } from 'antd'

const { Title, Paragraph } = Typography

export default function IntroductionScene({ scene }) {
  const cards = scene.content?.goal_cards || []
  return (
    <div className="classroom-scene-body">
      <Title level={4}>{scene.content?.question}</Title>
      <Paragraph>模型训练不是一次性猜答案，而是根据损失反馈不断修正参数。</Paragraph>
      <div className="goal-card-grid">
        {cards.map((item) => <Card key={item} size="small">{item}</Card>)}
      </div>
    </div>
  )
}
