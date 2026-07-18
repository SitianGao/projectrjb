import { List, Typography } from 'antd'

const { Title } = Typography

export default function SummaryScene({ scene }) {
  const content = scene.content || {}
  return (
    <div className="summary-scene">
      <Title level={4}>课堂学习总结</Title>
      <List header="已理解" dataSource={content.mastered || []} renderItem={(item) => <List.Item>{item}</List.Item>} />
      <List header="仍需巩固" dataSource={content.review || []} renderItem={(item) => <List.Item>{item}</List.Item>} />
      <List header="建议" dataSource={content.next || []} renderItem={(item) => <List.Item>{item}</List.Item>} />
    </div>
  )
}
