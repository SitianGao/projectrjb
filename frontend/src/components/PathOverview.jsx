import { Steps, Tag } from 'antd'
import {
  CheckCircleFilled,
  PlayCircleFilled,
  LockFilled,
  ExclamationCircleFilled,
} from '@ant-design/icons'
import { safeProgress } from '../utils/safeClamp'
import { normalizeTasks } from '../utils/stageUtils'

const STATUS_CONFIG = {
  completed: { icon: <CheckCircleFilled style={{ color: '#22C55E' }} />, color: '#22C55E', label: '已完成' },
  current: { icon: <PlayCircleFilled style={{ color: '#6C5CE7' }} />, color: '#6C5CE7', label: '进行中' },
  locked: { icon: <LockFilled style={{ color: '#D1D5DB' }} />, color: '#D1D5DB', label: '未解锁' },
  review: { icon: <ExclamationCircleFilled style={{ color: '#F59E0B' }} />, color: '#F59E0B', label: '需复习' },
}

/**
 * Compact horizontal step indicator replacing the old zigzag chart.
 * Height: ~140-180px. Shows stages as connected steps.
 */
export default function PathOverview({
  stages = [],
  currentStage = 1,
  onStageClick,
  activeStageId,
}) {
  if (!stages.length) return null

  const items = stages.map((stage, idx) => {
    const stageId = stage.stage_id || idx + 1
    let status
    if (stage.needsReview) {
      status = 'review'
    } else if (stageId < currentStage) {
      status = 'completed'
    } else if (stageId === currentStage) {
      status = 'current'
    } else {
      status = 'locked'
    }

    const cfg = STATUS_CONFIG[status]
    const tasks = normalizeTasks(stage.tasks)
    const { completed, total, percent } = safeProgress(
      tasks.filter((t) => t.status === 'completed').length,
      tasks.length,
    )
    const name = String(stage.title || `阶段${stageId}`).slice(0, 12)
    const isActive = activeStageId === stageId

    return {
      title: (
        <div
          onClick={() => onStageClick?.(stage, stageId)}
          style={{
            cursor: status === 'locked' ? 'default' : 'pointer',
            textAlign: 'center',
            padding: '4px 8px',
            borderRadius: 10,
            background: isActive ? '#F3F0FF' : 'transparent',
            border: isActive ? '1.5px solid #6C5CE7' : '1.5px solid transparent',
            transition: 'all 0.2s',
            minWidth: 100,
          }}
        >
          <div style={{ fontSize: 11, color: cfg.color, fontWeight: 600 }}>
            {cfg.label}
          </div>
          <div style={{
            fontSize: 13, fontWeight: isActive ? 600 : 400,
            color: status === 'locked' ? '#9CA3AF' : '#111827',
            margin: '2px 0',
          }}>
            {name}
          </div>
          {total > 0 && (
            <Tag
              color={status === 'completed' ? 'success' : status === 'current' ? 'purple' : 'default'}
              style={{ fontSize: 10, margin: 0, borderRadius: 6 }}
            >
              {completed}/{total}
            </Tag>
          )}
        </div>
      ),
      icon: cfg.icon,
      status: status === 'current' ? 'process' : status === 'completed' ? 'finish' : 'wait',
    }
  })

  return (
    <div style={{
      background: '#FFFFFF',
      borderRadius: 16,
      padding: '20px 24px',
      border: '1px solid #E5E7EB',
      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      maxWidth: 1440,
      margin: '0 auto 24px',
    }}>
      <div style={{ fontSize: 14, fontWeight: 600, color: '#111827', marginBottom: 16 }}>
        学习路径总览
      </div>
      <Steps
        current={currentStage - 1}
        items={items}
        size="small"
        style={{ overflow: 'auto' }}
        items={items.map((item, idx) => ({
          ...item,
          status: item.status,
        }))}
      />
    </div>
  )
}
