import { Card, Typography } from 'antd'
import AgentWorkflowStep from './AgentWorkflowStep'

const { Text } = Typography

export default function AgentWorkflowCard({ job }) {
  return (
    <Card className="agent-workflow-card" title="多智能体协同进度">
      <div className="agent-workflow-list">
        {job.steps.map((step) => <AgentWorkflowStep key={step.key} step={step} />)}
      </div>
      {job.message && <Text type={job.status === 'failed' ? 'danger' : 'secondary'}>{job.message}</Text>}
    </Card>
  )
}
