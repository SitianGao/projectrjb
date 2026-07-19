import { Empty, Spin } from 'antd'
import ChatMessageRenderer from './ChatMessageRenderer'

export default function MessageList({ messages, loading }) {
  if (!messages?.length) return <Empty description="开始一次课程画像对话" />
  return (
    <div className="profile-message-list">
      {messages.map((message, index) => (
        <ChatMessageRenderer key={message.id || `${message.role}-${message.client_message_id || index}`} message={message} />
      ))}
      {loading && (
        <div className="profile-message-loading">
          <Spin size="small" /> AI 画像助手正在分析你的学习信息...
        </div>
      )}
    </div>
  )
}
