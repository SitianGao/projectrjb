import { Skeleton, Space, Card } from 'antd'

/**
 * 加载骨架屏
 *
 * @param {Object} props
 * @param {'card'|'list'|'text'|'detail'} props.type - 骨架类型
 * @param {number} props.count - 重复数量（list 类型时生效）
 * @param {number} props.rows - 文本行数（text 类型时生效）
 */
export default function LoadingSkeleton({ type = 'card', count = 3, rows = 4 }) {
  if (type === 'list') {
    return (
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {Array.from({ length: count }, (_, i) => (
          <Card key={i}>
            <Skeleton active avatar paragraph={{ rows: 2 }} />
          </Card>
        ))}
      </Space>
    )
  }

  if (type === 'text') {
    return <Skeleton active paragraph={{ rows }} />
  }

  if (type === 'detail') {
    return (
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Skeleton active avatar paragraph={{ rows: 1 }} />
        <Skeleton active paragraph={{ rows: 6 }} />
      </Space>
    )
  }

  // card: 默认
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Skeleton active paragraph={{ rows: 1 }} />
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {Array.from({ length: count }, (_, i) => (
          <Card key={i} style={{ width: 300 }}>
            <Skeleton active paragraph={{ rows: 3 }} />
          </Card>
        ))}
      </div>
    </Space>
  )
}
