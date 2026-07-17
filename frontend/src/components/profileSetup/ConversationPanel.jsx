import { Card, Typography } from 'antd'
import MessageList from './MessageList'
import ProfileChatInput from './ProfileChatInput'
import ProfileQuickActions from './ProfileQuickActions'

const { Text } = Typography

export default function ConversationPanel({ messages, loading, error, onSend }) {
  return (
    <Card className="profile-conversation-card" title="课程画像 ChatBox">
      <Text type="secondary">建议 3 到 5 轮补齐关键信息。这里不会承担日常答疑，答疑请进入 AI 学习工作台。</Text>
      <ProfileQuickActions onPick={onSend} disabled={loading} />
      <MessageList messages={messages} loading={loading} />
      {error && <Text type="danger">{error.message || '对话失败，请重试'}</Text>}
      <ProfileChatInput onSend={onSend} loading={loading} />
    </Card>
  )
}
