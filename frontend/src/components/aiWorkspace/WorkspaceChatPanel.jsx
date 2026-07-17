import { useState } from 'react'
import { Button, Card, Input, Space, Typography } from 'antd'
import { SendOutlined } from '@ant-design/icons'

const { Paragraph } = Typography

export default function WorkspaceChatPanel({ messages, loading, onSend }) {
  const [value, setValue] = useState('')
  const submit = () => {
    const text = value.trim()
    if (!text) return
    onSend(text)
    setValue('')
  }
  return (
    <Card className="workspace-chat-panel" title="AI 导师">
      <div className="workspace-message-list">
        {messages.length === 0 && (
          <div className="workspace-empty-tip">可以询问当前知识点、让 AI 生成例题、解释选中内容或调整路径。</div>
        )}
        {messages.map((message, index) => (
          <div className={`workspace-message is-${message.role}`} key={`${message.role}-${index}`}>
            <strong>{message.role === 'user' ? '我' : 'AI 导师'}</strong>
            <Paragraph>{message.content}</Paragraph>
          </div>
        ))}
      </div>
      <Space className="workspace-fast-actions" wrap>
        {['解释当前知识点', '生成 3 道例题', '换一种方式讲解', '根据测评调整路径'].map((text) => (
          <Button key={text} onClick={() => onSend(text)} disabled={loading}>{text}</Button>
        ))}
      </Space>
      <div className="workspace-chat-input">
        <Input.TextArea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          autoSize={{ minRows: 2, maxRows: 4 }}
          placeholder="输入你的学习问题..."
        />
        <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={submit}>发送</Button>
      </div>
    </Card>
  )
}
