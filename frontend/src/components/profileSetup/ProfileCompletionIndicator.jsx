import { Progress, Typography } from 'antd'

const { Text } = Typography

export default function ProfileCompletionIndicator({ value = 0, canConfirm = false }) {
  const percent = Math.round(Math.max(0, Math.min(1, value)) * 100)
  return (
    <div className="profile-completion">
      <div>
        <Text strong>画像完整度</Text>
        <Text type="secondary">{canConfirm ? '核心维度已满足确认条件' : '继续通过自然对话补齐核心维度'}</Text>
      </div>
      <Progress type="circle" percent={percent} size={74} strokeColor="#6C5CE7" />
    </div>
  )
}
