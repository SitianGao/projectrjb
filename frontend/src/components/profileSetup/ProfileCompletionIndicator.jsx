import { Progress, Typography } from 'antd'

const { Text } = Typography

export default function ProfileCompletionIndicator({ value = 0 }) {
  const percent = Math.round(Math.max(0, Math.min(1, value)) * 100)
  return (
    <div className="profile-completion">
      <div>
        <Text strong>画像完整度</Text>
        <Text type="secondary">达到 85% 后可确认生成路径</Text>
      </div>
      <Progress type="circle" percent={percent} size={74} strokeColor="#6C5CE7" />
    </div>
  )
}
