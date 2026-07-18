import { Tooltip } from 'antd'
import {
  RobotOutlined,
  EditOutlined,
  ApartmentOutlined,
  BarChartOutlined,
} from '@ant-design/icons'

const TOOLS = [
  { key: 'tutor', icon: <RobotOutlined />, label: 'AI 导师' },
  { key: 'notes', icon: <EditOutlined />, label: '课堂笔记' },
  { key: 'knowledge', icon: <ApartmentOutlined />, label: '当前知识点' },
  { key: 'progress', icon: <BarChartOutlined />, label: '学习状态' },
]

export default function ClassroomFloatingToolbar({ activePanel, onPanelChange }) {
  return (
    <div
      style={{
        position: 'fixed',
        right: 16,
        top: '50%',
        transform: 'translateY(-50%)',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}
    >
      {TOOLS.map((tool) => {
        const isActive = activePanel === tool.key
        return (
          <Tooltip key={tool.key} title={tool.label} placement="left">
            <button
              onClick={() => onPanelChange(isActive ? null : tool.key)}
              className="classroom-floating-btn"
              style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: isActive ? '#6C5CE7' : 'rgba(255,255,255,0.85)',
                border: isActive ? 'none' : '1px solid rgba(0,0,0,0.08)',
                boxShadow: isActive
                  ? '0 4px 16px rgba(108,92,231,0.3)'
                  : '0 2px 8px rgba(0,0,0,0.06)',
                cursor: 'pointer',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                color: isActive ? '#fff' : '#6B7280',
                fontSize: 18,
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.transform = 'scale(1.1)'
                  e.currentTarget.style.color = '#6C5CE7'
                  e.currentTarget.style.borderColor = 'rgba(108,92,231,0.3)'
                  e.currentTarget.style.boxShadow = '0 4px 16px rgba(108,92,231,0.15)'
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.transform = 'scale(1)'
                  e.currentTarget.style.color = '#6B7280'
                  e.currentTarget.style.borderColor = 'rgba(0,0,0,0.08)'
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)'
                }
              }}
            >
              {tool.icon}
            </button>
          </Tooltip>
        )
      })}
    </div>
  )
}
