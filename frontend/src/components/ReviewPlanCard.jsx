import { useState } from 'react'
import { Button, Card, Empty, Modal, Space, Tag, Typography } from 'antd'
import {
  BookOutlined,
  ClockCircleOutlined,
  PlayCircleFilled,
  WarningFilled,
  CheckCircleOutlined,
  RightOutlined,
} from '@ant-design/icons'

const { Text, Paragraph } = Typography

const URGENCY_MAP = {
  high: { color: '#EF4444', label: '高优先级', icon: <WarningFilled /> },
  medium: { color: '#F59E0B', label: '中优先级', icon: <ClockCircleOutlined /> },
  low: { color: '#22C55E', label: '低优先级', icon: <CheckCircleOutlined /> },
}

function formatMinutes(minutes) {
  if (!minutes || minutes <= 0) return '--'
  if (minutes < 60) return `${minutes} 分钟`
  return `${Math.floor(minutes / 60)} 时 ${minutes % 60} 分`
}

/**
 * Right panel card — shows up to 3 review items for today.
 */
export default function ReviewPlanCard({
  plans = [],
  maxItems = 3,
  onViewAll,
  onStartReview,
  style,
}) {
  const [resourcesModal, setResourcesModal] = useState(null)

  if (!plans.length) {
    return (
      <Card
        style={{
          borderRadius: 16, border: '1px solid #E5E7EB',
          background: '#FFFFFF', minWidth: 0, width: '100%',
          ...style,
        }}
        styles={{ body: { padding: '18px 20px' } }}
      >
        <Text strong style={{ fontSize: 15, color: '#111827', display: 'block', marginBottom: 16 }}>
          📝 今日复习计划
        </Text>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="当前课程暂无需要复习的知识点"
          style={{ padding: '16px 0' }}
        />
      </Card>
    )
  }

  const visible = plans.slice(0, maxItems)
  const hasMore = plans.length > maxItems

  return (
    <Card
      style={{
        borderRadius: 16, border: '1px solid #E5E7EB',
        background: '#FFFFFF', minWidth: 0, width: '100%',
        ...style,
      }}
      styles={{ body: { padding: '18px 20px' } }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Text strong style={{ fontSize: 15, color: '#111827' }}>📝 今日复习计划</Text>
        <Tag color="orange" style={{ borderRadius: 6 }}>{plans.length} 项</Tag>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {visible.map((item, i) => {
          const uc = URGENCY_MAP[item.urgency] || URGENCY_MAP.medium
          const matchCount = item.resources?.length || 0

          return (
            <div
              key={i}
              style={{
                padding: '12px 14px',
                borderRadius: 12,
                border: `1px solid #E5E7EB`,
                borderLeft: `3px solid ${uc.color}`,
                background: '#FAFAFC',
                minWidth: 0,
              }}
            >
              {/* Topic + priority */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <Text strong style={{ fontSize: 14, color: '#111827' }}>{item.topic}</Text>
                <Tag color={item.urgency === 'high' ? 'red' : item.urgency === 'medium' ? 'orange' : 'green'} style={{ borderRadius: 6, margin: 0 }}>
                  {uc.icon} {uc.label}
                </Tag>
              </div>

              {/* Reason */}
              <Paragraph
                type="secondary"
                style={{ fontSize: 12, lineHeight: 1.6, marginBottom: 8, minWidth: 0, wordBreak: 'break-word' }}
                ellipsis={{ rows: 2 }}
              >
                {item.reason || '建议巩固该知识点'}
              </Paragraph>

              {/* Meta info */}
              <Space size={12} wrap style={{ marginBottom: 8 }}>
                {item.recommended_resources?.length > 0 && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    建议：{item.recommended_resources.slice(0, 2).join('、')}
                  </Text>
                )}
                {item.estimated_minutes && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    <ClockCircleOutlined /> {formatMinutes(item.estimated_minutes)}
                  </Text>
                )}
              </Space>

              {/* Matched resources hint */}
              {matchCount > 0 && (
                <Button
                  type="link"
                  size="small"
                  icon={<BookOutlined />}
                  onClick={() => setResourcesModal(item)}
                  style={{ padding: 0, fontSize: 12, color: '#6C5CE7' }}
                >
                  已匹配 {matchCount} 项学习资源
                </Button>
              )}

              {/* Start review button */}
              <div style={{ marginTop: 8 }}>
                <Button
                  size="small"
                  type="primary"
                  ghost
                  icon={<PlayCircleFilled />}
                  onClick={() => onStartReview?.(item)}
                  style={{ borderRadius: 6, borderColor: '#6C5CE7', color: '#6C5CE7' }}
                >
                  开始复习
                </Button>
              </div>
            </div>
          )
        })}

        {hasMore && (
          <Button
            type="link"
            icon={<RightOutlined />}
            onClick={onViewAll}
            style={{ color: '#6C5CE7', padding: 0 }}
          >
            查看全部复习计划
          </Button>
        )}
      </div>

      {/* Resources modal */}
      <Modal
        title={resourcesModal ? `复习资源：${resourcesModal.topic}` : ''}
        open={!!resourcesModal}
        onCancel={() => setResourcesModal(null)}
        footer={null}
        width={480}
      >
        {resourcesModal?.resources?.map((res, i) => (
          <div key={res.id || i} style={{
            padding: '8px 12px', borderRadius: 8,
            border: '1px solid #E5E7EB', marginBottom: 6,
            fontSize: 13, color: '#374151',
          }}>
            <BookOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />
            {res.title}
          </div>
        ))}
      </Modal>
    </Card>
  )
}
