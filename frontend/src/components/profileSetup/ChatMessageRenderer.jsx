import { Typography } from 'antd'

const { Paragraph } = Typography

export default function ChatMessageRenderer({ message }) {
  return (
    <div className={`profile-message profile-message--${message.role}`}>
      <span className="profile-message-role">{message.role === 'user' ? '我' : 'AI'}</span>
      <Paragraph>{message.content}</Paragraph>
    </div>
  )
}
