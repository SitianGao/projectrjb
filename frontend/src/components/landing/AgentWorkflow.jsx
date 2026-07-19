import {
  UserOutlined,
  CompassOutlined,
  BookOutlined,
  RobotOutlined,
  BarChartOutlined,
} from '@ant-design/icons'

const AGENTS = [
  { id: 'profile', icon: <UserOutlined />, name: 'ProfileAgent', label: '理解学生', color: '#6256e8' },
  { id: 'planner', icon: <CompassOutlined />, name: 'PlannerAgent', label: '规划学习', color: '#258cf4' },
  { id: 'resource', icon: <BookOutlined />, name: 'ResourceAgent', label: '准备内容', color: '#2ac99a' },
  { id: 'tutor', icon: <RobotOutlined />, name: 'TutorAgent', label: '实时辅导', color: '#fa8c16' },
  { id: 'evaluate', icon: <BarChartOutlined />, name: 'EvaluateAgent', label: '诊断反馈', color: '#eb2f96' },
]

function AgentNode({ agent, delay }) {
  return (
    <div className="lp-agent-node" style={{ '--agent-color': agent.color, animationDelay: `${delay}ms` }}>
      <div className="lp-agent-node__icon lp-agent-node__icon--breathe" style={{ background: `${agent.color}15`, color: agent.color }}>
        {agent.icon}
      </div>
      <span className="lp-agent-node__name">{agent.name}</span>
      <span className="lp-agent-node__label">{agent.label}</span>
    </div>
  )
}

function Connector() {
  return (
    <div className="lp-agent-connector">
      <div className="lp-agent-connector__line" />
      <div className="lp-agent-connector__arrow">›</div>
    </div>
  )
}

export default function AgentWorkflow() {
  return (
    <section className="lp-agents" id="agents">
      <div className="lp-section__header">
        <h2 className="lp-section__title">五个 Agent，协同完成一次完整学习决策</h2>
        <p className="lp-section__subtitle">
          从理解学生到诊断反馈，每个 Agent 负责一个专业环节，共同构建自适应学习闭环。
        </p>
      </div>

      <div className="lp-agents__flow">
        {/* Top row: Student Input → ProfileAgent → PlannerAgent */}
        <div className="lp-agents__row">
          <div className="lp-agents__start">
            <div className="lp-agents__start-icon">
              <UserOutlined />
            </div>
            <span>学生输入</span>
          </div>
          <Connector />
          <AgentNode agent={AGENTS[0]} delay={0} />
          <Connector />
          <AgentNode agent={AGENTS[1]} delay={100} />
        </div>

        {/* Middle: Planner branches to Resource */}
        <div className="lp-agents__branch">
          <div className="lp-agents__branch-line" />
          <div className="lp-agents__row lp-agents__row--center">
            <AgentNode agent={AGENTS[2]} delay={200} />
          </div>
        </div>

        {/* Output */}
        <div className="lp-agents__output">
          <div className="lp-agents__output-line" />
          <div className="lp-agents__output-box">
            <BookOutlined style={{ marginRight: 6 }} />
            学习任务与个性化资源
          </div>
        </div>

        {/* Bottom: Tutor + Evaluate */}
        <div className="lp-agents__row lp-agents__row--bottom">
          <AgentNode agent={AGENTS[3]} delay={300} />
          <span className="lp-agents__plus">+</span>
          <AgentNode agent={AGENTS[4]} delay={400} />
        </div>

        {/* Final output */}
        <div className="lp-agents__final">
          <div className="lp-agents__final-line" />
          <div className="lp-agents__final-box">
            <BarChartOutlined style={{ marginRight: 6 }} />
            画像更新与路径调整
          </div>
        </div>
      </div>

      {/* Mobile: vertical flow */}
      <div className="lp-agents__flow-mobile">
        <div className="lp-agents__mobile-start">
          <UserOutlined /> 学生输入
        </div>
        {AGENTS.map((agent, i) => (
          <div key={agent.id} className="lp-agents__mobile-step">
            <div className="lp-agents__mobile-line" />
            <AgentNode agent={agent} delay={i * 100} />
          </div>
        ))}
        <div className="lp-agents__mobile-line" />
        <div className="lp-agents__mobile-output">
          画像更新与路径调整
        </div>
      </div>
    </section>
  )
}
