import { Card, Typography } from 'antd'

const { Title } = Typography

export default function DiscussionScene({ scene }) {
  return (
    <div>
      <Title level={4}>{scene.content?.question}</Title>
      <div className="discussion-grid">
        {(scene.content?.viewpoints || []).map((item) => <Card key={item}>{item}</Card>)}
      </div>
    </div>
  )
}
