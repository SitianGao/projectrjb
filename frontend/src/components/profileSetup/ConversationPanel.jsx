import { Card, Typography } from 'antd'
import MessageList from './MessageList'
import ProfileChatInput from './ProfileChatInput'

const { Text, Title } = Typography

export default function ConversationPanel({ title, description, messages, loading, error, onSend }) {
  return (
    <Card className="profile-conversation-card">
      <div className="profile-chat-header">
        <Title level={3}>{title}</Title>
        <Text type="secondary">{description}</Text>
      </div>
      <MessageList messages={messages} loading={loading} />
      {error && <Text type="danger">{error.message || '对话失败，请重试'}</Text>}
      <ProfileChatInput onSend={onSend} loading={loading} />
    </Card>
  )
}
