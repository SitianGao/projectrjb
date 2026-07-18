import { Alert, Button, Card, Skeleton, Space, Typography } from 'antd'
import { ThunderboltOutlined } from '@ant-design/icons'
import ProfileCompletionIndicator from './ProfileCompletionIndicator'
import ProfileDimensionCard from './ProfileDimensionCard'

const { Text, Title } = Typography

const GROUPS = [
  { title: '核心目标', keys: ['learning_goal', 'knowledge_foundation', 'weak_points'] },
  { title: '学习偏好', keys: ['cognitive_style', 'preferred_resources', 'assessment_preference'] },
  { title: '时间安排', keys: ['session_duration_minutes', 'sessions_per_week', 'weekly_available_hours', 'target_duration_weeks', 'preferred_study_time'] },
  { title: '其他信息', keys: ['learning_history', 'interest_directions'] },
]

function dimensionsByKey(dimensions = []) {
  return dimensions.reduce((acc, item) => {
    acc[item.key] = item
    return acc
  }, {})
}

export default function LiveProfilePanel({
  profileState,
  loading,
  highlightKeys = [],
  generating,
  generationJob,
  generationError,
  onConfirm,
}) {
  if (loading) return <Card className="profile-live-panel"><Skeleton active paragraph={{ rows: 8 }} /></Card>
  const dimensions = profileState?.dimensions || []
  const byKey = dimensionsByKey(dimensions)
  const canConfirm = Boolean(profileState?.can_confirm || profileState?.ready_for_confirmation)
  const missingRequired = profileState?.missing_required_dimensions || []
  const filledCount = dimensions.filter((item) => item.filled && item.required).length
  const requiredCount = dimensions.filter((item) => item.required).length
  const missingText = missingRequired.map((item) => item.label).join('、')
  return (
    <Card className="profile-live-panel">
      <div className="profile-live-header">
        <Title level={4}>实时课程画像</Title>
        <Text type="secondary">已完成 {filledCount} / {requiredCount} 个核心维度</Text>
      </div>
      <ProfileCompletionIndicator
        value={profileState?.completion_rate || profileState?.profile_completion_rate || 0}
        canConfirm={canConfirm}
      />
      <div className="profile-dimensions">
        {GROUPS.map((group) => (
          <section className="profile-dimension-group" key={group.title}>
            <Text strong>{group.title}</Text>
            <div className="profile-dimension-grid">
              {group.keys
                .map((key) => byKey[key])
                .filter(Boolean)
                .map((item) => (
                  <ProfileDimensionCard
                    key={item.key}
                    item={item}
                    missing={!item.filled}
                    highlighted={highlightKeys.includes(item.key)}
                  />
                ))}
            </div>
          </section>
        ))}
      </div>
      <div className="profile-confirm-footer">
        {!canConfirm ? (
          <Text type="secondary">还需补充：{missingText || '核心画像信息'}</Text>
        ) : (
          <Text>画像信息已足够，可以生成个性化学习路径。</Text>
        )}
        {generationError && <Alert type="error" showIcon message={generationError.message || '生成失败'} />}
        {generating && (
          <Text type="secondary">
            {generationJob?.steps?.find?.((step) => step.status === 'running')?.title || 'PlannerAgent 正在生成学习路径'}
          </Text>
        )}
        <Space direction="vertical" size={8} style={{ width: '100%' }}>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            block
            disabled={!canConfirm}
            loading={generating}
            onClick={onConfirm}
          >
            确认画像并生成学习路径
          </Button>
        </Space>
      </div>
    </Card>
  )
}
