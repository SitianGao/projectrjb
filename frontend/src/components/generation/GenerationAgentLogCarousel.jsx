import { AGENTS } from './generationAgents'

export default function GenerationAgentLogCarousel({ activeStepIndex }) {
  // Show agents whose index <= current step (they're "working")
  const activeAgents = AGENTS.filter((_, i) => i <= activeStepIndex)

  // Duplicate for seamless loop
  const items = [...activeAgents, ...activeAgents]

  return (
    <div className="gen-agent-log">
      <div className="gen-agent-log-track">
        {items.map((agent, i) => (
          <div key={i} className="gen-agent-log-item">
            <div
              className="gen-agent-log-icon"
              style={{ background: agent.bg, color: agent.color }}
            >
              {agent.icon}
            </div>
            <span style={{ fontWeight: 600, color: '#374151' }}>{agent.name}</span>
            <span style={{ color: '#9CA3AF' }}>·</span>
            <span>{agent.logMessage}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
