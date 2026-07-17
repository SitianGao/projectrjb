import { Empty } from 'antd'

export default function ConversationList({ items = [] }) {
  if (!items.length) return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无会话" />
  return (
    <div className="workspace-conversation-list">
      {items.map((item) => (
        <button key={item.id} className="workspace-conversation-item">
          <strong>{item.title}</strong>
          <span>{item.updatedAt}</span>
        </button>
      ))}
    </div>
  )
}
