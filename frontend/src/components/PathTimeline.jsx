import { Steps, Tag, Typography, Button, Space, Tooltip } from 'antd'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  PlayCircleOutlined,
  LockOutlined,
} from '@ant-design/icons'

const { Text, Title } = Typography

const statusIconMap = {
  completed: <CheckCircleOutlined />,
  in_progress: <PlayCircleOutlined />,
  pending: <ClockCircleOutlined />,
  locked: <LockOutlined />,
}

const statusLabelMap = {
  completed: { label: '已完成', color: 'success' },
  in_progress: { label: '进行中', color: 'processing' },
  pending: { label: '待开始', color: 'default' },
  locked: { label: '未解锁', color: 'default' },
}

/**
 * 学习路径时间线/步骤条
 *
 * @param {Object} props
 * @param {Array} props.nodes - 路径节点
 * @param {string} props.nodes[].id
 * @param {string} props.nodes[].title - 节点标题
 * @param {string} props.nodes[].description - 节点描述
 * @param {'completed'|'in_progress'|'pending'|'locked'} props.nodes[].status
 * @param {string} props.nodes[].duration - 预计时长
 * @param {Function} props.onNodeClick - (node) => void
 * @param {boolean} props.loading
 */
export default function PathTimeline({ nodes = [], onNodeClick, loading = false }) {
  if (loading) {
    return <Steps direction="vertical" current={-1} items={[]} />
  }

  if (!nodes.length) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <Text type="secondary">暂无学习路径，请先生成</Text>
      </div>
    )
  }

  const items = nodes.map((node, index) => {
    const statusInfo = statusLabelMap[node.status] || statusLabelMap.pending
    const isClickable = node.status !== 'locked'

    return {
      title: (
        <Space>
          <Text strong={node.status === 'in_progress'}>{node.title}</Text>
          <Tag color={statusInfo.color}>{statusInfo.label}</Tag>
          {node.duration && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {node.duration}
            </Text>
          )}
        </Space>
      ),
      description: (
        <div>
          {node.description && (
            <Text type="secondary">{node.description}</Text>
          )}
          {isClickable && onNodeClick && (
            <div style={{ marginTop: 4 }}>
              <Button
                type="link"
                size="small"
                onClick={() => onNodeClick(node)}
                style={{ padding: 0 }}
              >
                查看详情 →
              </Button>
            </div>
          )}
        </div>
      ),
      icon: statusIconMap[node.status],
      status: node.status === 'completed' ? 'finish' : node.status === 'in_progress' ? 'process' : 'wait',
    }
  })

  return (
    <div>
      <Title level={5} style={{ marginBottom: 16 }}>学习路径</Title>
      <Steps direction="vertical" current={-1} items={items} />
    </div>
  )
}
