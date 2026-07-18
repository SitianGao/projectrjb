import { Button, Card, Progress, Space, Tag, Typography } from 'antd'
import {
  BookOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  PlayCircleFilled,
  RightOutlined,
} from '@ant-design/icons'
import { safeProgress } from '../utils/safeClamp'

const { Text } = Typography

/**
 * Right panel card — shows current stage summary and next task.
 */
export default function CurrentLearningCard({
  stageTitle = '',
  stageId,
  nextTaskTitle = '',
  estimatedMinutes = 20,
  completedTasks = 0,
  totalTasks = 1,
  onContinue,
  onViewResources,
  style,
}) {
  const { completed, total, percent } = safeProgress(completedTasks, totalTasks)

  return (
    <Card
      style={{
        borderRadius: 16,
        border: '1px solid var(--border)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
        background: 'var(--bg-card)',
        minWidth: 0,
        width: '100%',
        ...style,
      }}
      styles={{ body: { padding: '18px 20px' } }}
    >
      <Text strong style={{ fontSize: 15, color: 'var(--text-primary)', display: 'block', marginBottom: 14 }}>
        📍 当前学习安排
      </Text>

      {/* Current stage */}
      <div style={{
        background: 'var(--tint-primary)', borderRadius: 10,
        padding: '10px 14px', marginBottom: 14,
      }}>
        <Text type="secondary" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 }}>
          当前阶段
        </Text>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
          阶段{stageId}：{stageTitle}
        </div>
      </div>

      {/* Next task */}
      <div style={{ marginBottom: 14 }}>
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
          下一步任务
        </Text>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '8px 12px', borderRadius: 8,
          background: 'var(--surface-secondary)', border: '1px solid var(--border)',
        }}>
          <BookOutlined style={{ color: '#6C5CE7' }} />
          <Text style={{ fontSize: 13, color: 'var(--text-primary)', flex: 1 }}>{nextTaskTitle || '暂无任务'}</Text>
        </div>
      </div>

      {/* Time estimate */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 14 }}>
        <ClockCircleOutlined style={{ color: '#6C5CE7', fontSize: 13 }} />
        <Text style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          预计用时 {estimatedMinutes} 分钟
        </Text>
      </div>

      {/* Stage progress */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <Text style={{ fontSize: 12, color: 'var(--text-secondary)' }}>本阶段进度</Text>
          <Text style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{completed}/{total}</Text>
        </div>
        <Progress percent={percent} size="small" strokeColor="#6C5CE7" style={{ margin: 0 }} />
      </div>

      {/* Action buttons */}
      <Space direction="vertical" style={{ width: '100%' }} size={8}>
        <Button
          type="primary"
          block
          icon={<PlayCircleFilled />}
          onClick={onContinue}
          style={{
            borderRadius: 8,
            background: '#6C5CE7',
            borderColor: '#6C5CE7',
          }}
        >
          继续学习
        </Button>
        <Button
          block
          icon={<FileTextOutlined />}
          onClick={onViewResources}
          style={{ borderRadius: 8 }}
        >
          查看阶段资源
        </Button>
      </Space>
    </Card>
  )
}
