import { Steps, Typography } from 'antd'

const { Title, Paragraph } = Typography

export default function WhiteboardScene({ scene }) {
  return (
    <div className="whiteboard-scene">
      <Title level={4}>{scene.content?.formula}</Title>
      <Paragraph>每一轮训练都根据梯度调整参数，学习率决定这一步迈多大。</Paragraph>
      <Steps direction="vertical" items={(scene.content?.steps || []).map((step) => ({ title: step }))} />
    </div>
  )
}
