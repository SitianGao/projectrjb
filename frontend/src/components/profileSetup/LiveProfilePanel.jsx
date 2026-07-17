import { Card, Skeleton, Typography } from 'antd'
import ProfileCompletionIndicator from './ProfileCompletionIndicator'
import ProfileDimensionCard from './ProfileDimensionCard'

const { Text } = Typography

export default function LiveProfilePanel({ profileState, loading }) {
  if (loading) return <Card className="profile-live-panel"><Skeleton active paragraph={{ rows: 8 }} /></Card>
  const filled = profileState?.filled_dimensions || []
  const missing = profileState?.missing_dimensions || []
  return (
    <Card className="profile-live-panel" title="实时课程画像">
      <ProfileCompletionIndicator value={profileState?.completion_rate || 0} />
      <div className="profile-dimension-grid">
        {filled.map((item) => <ProfileDimensionCard key={item.key} item={item} />)}
        {missing.map((item) => <ProfileDimensionCard key={item.key} item={item} missing />)}
      </div>
      <Text type="secondary">画像只作用于当前课程，不会覆盖其他课程的学习路径和历史记录。</Text>
    </Card>
  )
}
