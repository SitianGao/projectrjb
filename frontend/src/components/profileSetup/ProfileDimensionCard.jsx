import { Card, Tag, Typography } from 'antd'
import { CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons'

const { Text } = Typography

export default function ProfileDimensionCard({ item, missing }) {
  const value = Array.isArray(item.value) ? item.value.join('、') : item.value
  return (
    <Card size="small" className={`profile-dimension-card${missing ? ' is-missing' : ''}`}>
      <div className="profile-dimension-title">
        {missing ? <ExclamationCircleOutlined /> : <CheckCircleOutlined />}
        <Text strong>{item.label}</Text>
        <Tag color={missing ? 'default' : 'purple'}>{missing ? '待补充' : '已记录'}</Tag>
      </div>
      <Text type="secondary">{value || '继续通过对话补齐'}</Text>
    </Card>
  )
}
