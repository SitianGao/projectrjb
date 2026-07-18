import { Card, Typography } from 'antd'

const { Title, Paragraph } = Typography

export default function PresentationScene({ scene }) {
  return (
    <div className="slide-grid">
      {(scene.content?.slides || []).map((slide) => (
        <Card key={slide.title} className="presentation-slide">
          <Title level={4}>{slide.title}</Title>
          <Paragraph>{slide.body}</Paragraph>
        </Card>
      ))}
    </div>
  )
}
