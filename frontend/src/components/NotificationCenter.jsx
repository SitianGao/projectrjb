import { useState } from 'react'
import { Modal, List, Typography, Tag, Badge, Button, Empty } from 'antd'
import {
  BellOutlined,
  TrophyOutlined,
  BookOutlined,
  RobotOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'

const { Text } = Typography

// Mock 通知数据
const MOCK_NOTIFICATIONS = [
  {
    id: 1,
    icon: <TrophyOutlined style={{ color: '#fa8c16' }} />,
    title: '学习评估已生成',
    desc: '你的最新六维学习画像评估报告已生成，综合评分 78 分，持续进步中。',
    time: '10 分钟前',
    tag: { text: '新', color: 'red' },
  },
  {
    id: 2,
    icon: <BookOutlined style={{ color: '#1677ff' }} />,
    title: '新资源推荐',
    desc: '根据你的薄弱环节，AI 为你推荐了 3 份英语语法专项练习资源。',
    time: '1 小时前',
    tag: null,
  },
  {
    id: 3,
    icon: <RobotOutlined style={{ color: '#8b5cf6' }} />,
    title: 'AI 辅导建议',
    desc: '你的辅导老师建议本周重点攻克二次函数压轴题，已更新学习路径。',
    time: '3 小时前',
    tag: null,
  },
  {
    id: 4,
    icon: <ThunderboltOutlined style={{ color: '#52c41a' }} />,
    title: '学习路径已更新',
    desc: '基于最近的评估数据，AI 已自动优化你的学习路径第二阶段任务安排。',
    time: '昨天',
    tag: null,
  },
  {
    id: 5,
    icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    title: '任务完成提醒',
    desc: '你已完成本周所有学习任务，继续保持！',
    time: '2 天前',
    tag: null,
  },
]

export default function NotificationCenter({ children }) {
  const [open, setOpen] = useState(false)
  const [notifications] = useState(MOCK_NOTIFICATIONS)
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
