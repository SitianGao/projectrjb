import { Typography } from 'antd'
import { RobotOutlined, UserOutlined } from '@ant-design/icons'

const { Paragraph } = Typography

// ── Agent → student-facing name mapping ──
const AGENT_DISPLAY_NAMES = {
  ProfileAgent: 'AI 画像助手',
  PlannerAgent: 'AI 学习规划助手',
  TutorAgent: 'AI 学习导师',
  EvaluateAgent: 'AI 学习评估助手',
  ResourceAgent: 'AI 资源助手',
}

/**
 * Development-only debug meta. Only shown when:
 *   1. Running in dev mode (import.meta.env.DEV)
 *   2. Env var VITE_SHOW_AGENT_DEBUG is explicitly set to 'true'
 */
const SHOW_AGENT_DEBUG =
  import.meta.env.DEV &&
  import.meta.env.VITE_SHOW_AGENT_DEBUG === 'true'

function AgentDebugMeta({ agentRun }) {
  if (!agentRun) return null
  const duration = Number(agentRun.duration_ms || 0)
  return (
    <div className="profile-agent-debug" style={{ marginTop: 8, padding: '6px 10px', background: '#F9FAFB', borderRadius: 8, fontSize: 12, color: '#9CA3AF' }}>
      {agentRun.agent_name && <span>{agentRun.agent_name}</span>}
      {agentRun.provider && <span> | {agentRun.provider}</span>}
      {agentRun.model && <span> | {agentRun.model}</span>}
      {agentRun.status && <span> | {agentRun.status}</span>}
      {duration > 0 && <span> | {duration} ms</span>}
      {agentRun.fallback_used && <span style={{ color: '#F59E0B' }}> | 降级</span>}
    </div>
  )
}

function getDisplayName(message) {
  const agentName = message?.agent_run?.agent_name
  if (agentName && AGENT_DISPLAY_NAMES[agentName]) {
    return AGENT_DISPLAY_NAMES[agentName]
  }
  // Generic fallback for messages with agent_run but unknown agent
  if (message?.agent_run?.agent_name) return 'AI 助手'
  // Default for this page context
  return 'AI 画像助手'
}

export default function ChatMessageRenderer({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`profile-message profile-message--${message.role}`}>
      <span className="profile-message-role">
        {isUser ? (
          <><UserOutlined style={{ marginRight: 4 }} />我</>
        ) : (
          <><RobotOutlined style={{ marginRight: 4 }} />{getDisplayName(message)}</>
        )}
      </span>
      <div className="profile-message-body">
        <Paragraph>{message.content}</Paragraph>
        {SHOW_AGENT_DEBUG && !isUser && <AgentDebugMeta agentRun={message.agent_run} />}
      </div>
    </div>
  )
}
