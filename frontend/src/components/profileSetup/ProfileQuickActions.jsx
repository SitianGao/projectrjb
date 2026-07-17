import { Button, Space } from 'antd'
import { BulbOutlined, FieldTimeOutlined, ReadOutlined } from '@ant-design/icons'

const QUICK_ACTIONS = [
  { icon: <BulbOutlined />, text: '我想系统学习人工智能，目标是能做课程项目。' },
  { icon: <ReadOutlined />, text: '我有一点 Python 基础，但数学和算法比较薄弱。' },
  { icon: <FieldTimeOutlined />, text: '我希望每天晚上学习 30 分钟，更喜欢图解、案例和练习。' },
]

export default function ProfileQuickActions({ onPick, disabled }) {
  return (
    <Space wrap className="profile-quick-actions">
      {QUICK_ACTIONS.map((item) => (
        <Button key={item.text} icon={item.icon} onClick={() => onPick(item.text)} disabled={disabled}>
          {item.text}
        </Button>
      ))}
    </Space>
  )
}
