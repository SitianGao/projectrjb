import { Button, Card, Checkbox, Space, Typography } from 'antd'
import { ThunderboltOutlined } from '@ant-design/icons'
import ProfileSummaryCard from './ProfileSummaryCard'

const { Text } = Typography

export default function ProfileConfirmationCard({ ready, confirmed, onConfirmChange, onGenerate, loading, summary }) {
  return (
    <Card className="profile-confirm-card" title="确认后生成学习路径">
      <ProfileSummaryCard summary={summary} />
      {!ready && <Text type="secondary">请继续补充右侧缺失维度，系统不会自动生成路径。</Text>}
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        <Checkbox checked={confirmed} disabled={!ready || loading} onChange={(event) => onConfirmChange(event.target.checked)}>
          我确认以上画像可用于生成本课程学习路径
        </Checkbox>
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          block
          disabled={!ready || !confirmed}
          loading={loading}
          onClick={onGenerate}
        >
          生成学习路径与资源蓝图
        </Button>
      </Space>
    </Card>
  )
}
