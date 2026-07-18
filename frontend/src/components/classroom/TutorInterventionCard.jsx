import { Alert } from 'antd'

export default function TutorInterventionCard({ intervention }) {
  if (!intervention?.need_intervention && !intervention?.should_intervene) return null

  return (
    <Alert
      className="tutor-intervention-card"
      type="warning"
      showIcon
      message={intervention.message || 'AI 导师建议你先放慢一步'}
      description={intervention.suggestion || '当前操作可能导致理解偏差，建议回到讲义或模拟实验重新观察。'}
    />
  )
}
