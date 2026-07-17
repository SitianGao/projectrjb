import { Button, Card, Typography } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import ConversationList from './ConversationList'

const { Text } = Typography

export default function ConversationSidebar() {
  return (
    <Card className="workspace-sidebar">
      <div className="workspace-sidebar-head">
        <Text strong>课程会话</Text>
        <Button size="small" icon={<PlusOutlined />}>新建</Button>
      </div>
      <ConversationList items={[{ id: 'current', title: '当前学习问题', updatedAt: '刚刚' }]} />
    </Card>
  )
}
