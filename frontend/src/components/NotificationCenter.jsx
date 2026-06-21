import { useState } from 'react'
import { Modal, List, Typography, Tag, Badge, Button, Empty } from 'antd'
import {
  BellOutlined,
} from '@ant-design/icons'

const { Text } = Typography

export default function NotificationCenter({ children }) {
  const [open, setOpen] = useState(false)
  const [notifications] = useState([])
  const unreadCount = notifications.filter((n) => n.tag?.text === '新').length

  return (
    <>
      {/* 触发器 */}
      <div onClick={() => setOpen(true)} style={{ cursor: 'pointer' }}>
        {children || (
          <Badge count={unreadCount} size="small" offset={[-2, 2]}>
            <div className="top-home-btn" title="通知">
              <BellOutlined />
            </div>
          </Badge>
        )}
      </div>

      {/* 居中弹窗 */}
      <Modal
        title={
          <span style={{ fontSize: 17 }}>
            <BellOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />
            通知中心
          </span>
        }
        open={open}
        onCancel={() => setOpen(false)}
        footer={null}
        width={520}
        centered
        styles={{ body: { padding: '8px 24px 20px', maxHeight: '60vh', overflowY: 'auto' } }}
      >
        {notifications.length === 0 ? (
          <Empty description="暂无通知" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <List
            dataSource={notifications}
            renderItem={(item) => (
              <List.Item style={{ padding: '14px 0', borderBottom: '1px solid var(--border, #f0f0f0)' }}>
                <div style={{ display: 'flex', gap: 12, width: '100%' }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                    background: '#f5f3ff', display: 'flex',
                    alignItems: 'center', justifyContent: 'center',
                    fontSize: 16,
                  }}>
                    {item.icon}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <Text strong style={{ fontSize: 14 }}>{item.title}</Text>
                      {item.tag && <Tag color={item.tag.color} style={{ fontSize: 11, lineHeight: '18px', padding: '0 6px' }}>{item.tag.text}</Tag>}
                    </div>
                    <Text type="secondary" style={{ fontSize: 13, lineHeight: 1.6 }}>{item.desc}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 11, color: '#bfbfbf' }}>{item.time}</Text>
                  </div>
                </div>
              </List.Item>
            )}
          />
        )}
      </Modal>
    </>
  )
}
