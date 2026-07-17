import { CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined, ClockCircleOutlined } from '@ant-design/icons'

const ICONS = {
  done: <CheckCircleOutlined />,
  running: <LoadingOutlined />,
  failed: <CloseCircleOutlined />,
  waiting: <ClockCircleOutlined />,
}

export default function AgentWorkflowStep({ step }) {
  return (
    <div className={`agent-workflow-step is-${step.status}`}>
      <span>{ICONS[step.status] || ICONS.waiting}</span>
      <div>
        <strong>{step.title}</strong>
        {step.message && <p>{step.message}</p>}
      </div>
    </div>
  )
}
