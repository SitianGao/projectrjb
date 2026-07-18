import { Button, Space } from 'antd'
import { FileSearchOutlined, HighlightOutlined, QuestionCircleOutlined } from '@ant-design/icons'

const QUICK_ACTIONS = [
  { key: 'explain_selection', label: '解释选中内容', icon: <HighlightOutlined /> },
  { key: 'generate_example', label: '生成例题', icon: <QuestionCircleOutlined /> },
  { key: 'explain_differently', label: '换一种方式讲解', icon: <FileSearchOutlined /> },
]

export default function TutorQuickActions({ onAsk }) {
  return (
    <Space wrap className="tutor-quick-actions">
      {QUICK_ACTIONS.map((item) => (
        <Button key={item.key} size="small" icon={item.icon} onClick={() => onAsk?.(item.label, { action: item.key })}>
          {item.label}
        </Button>
      ))}
    </Space>
  )
}
