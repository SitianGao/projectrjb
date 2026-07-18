import { Space, Tag, Typography } from 'antd'

const { Paragraph, Text } = Typography

function renderAgentRun(agentRun) {
  if (!agentRun) return null
  const duration = Number(agentRun.duration_ms || 0)
  return (
    <div className="profile-agent-run">
      <Space size={6} wrap>
        <Text type="secondary">{agentRun.agent_name || 'ProfileAgent'}</Text>
        {agentRun.provider && <Tag>{agentRun.provider}</Tag>}
        {agentRun.model && <Tag>{agentRun.model}</Tag>}
        {agentRun.status && <Tag color={agentRun.status === 'completed' ? 'green' : 'orange'}>{agentRun.status}</Tag>}
        {duration > 0 && <Text type="secondary">{duration} ms</Text>}
      </Space>
      {agentRun.fallback_used && (
        <Text type="warning">本轮使用了规则化降级结果，建议稍后重新尝试。</Text>
      )}
    </div>
  )
}

export default function ChatMessageRenderer({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`profile-message profile-message--${message.role}`}>
      <span className="profile-message-role">{isUser ? '我' : 'ProfileAgent'}</span>
      <div className="profile-message-body">
        <Paragraph>{message.content}</Paragraph>
        {!isUser && renderAgentRun(message.agent_run)}
      </div>
    </div>
  )
}
