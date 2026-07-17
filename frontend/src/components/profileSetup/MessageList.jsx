import { Empty, Spin } from 'antd'
import ChatMessageRenderer from './ChatMessageRenderer'

export default function MessageList({ messages, loading }) {
  if (!messages?.length) return <Empty description="开始一次课程画像对话" />
  return (
    <div className="profile-message-list">
      {messages.map((message, index) => (
        <ChatMessageRenderer key={`${message.role}-${index}`} message={message} />
      ))}
      {loading && <div className="profile-message-loading"><Spin size="small" /> 正在分析画像更新...</div>}
    </div>
  )
}
