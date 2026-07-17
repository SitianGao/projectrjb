import { Tooltip } from 'antd'
import {
  AimOutlined,
  BookOutlined,
  CheckCircleFilled,
  EditOutlined,
  LockOutlined,
  NodeIndexOutlined,
  PlayCircleFilled,
  UnorderedListOutlined,
} from '@ant-design/icons'

const TASK_TYPES = {
  objective: { label: '学习目标', icon: <AimOutlined /> },
  lecture: { label: '核心讲义', icon: <BookOutlined /> },
  diagram: { label: '概念图解', icon: <NodeIndexOutlined /> },
  quiz: { label: '知识检查', icon: <EditOutlined /> },
  exam: { label: '阶段测评', icon: <CheckCircleFilled /> },
}

const STATUS_STYLES = {
  completed: {
    icon: <CheckCircleFilled style={{ color: '#6C5CE7', fontSize: 18 }} />,
    bg: '#F3F0FF',
    border: '#6C5CE7',
    textColor: '#111827',
    dot: '#6C5CE7',
  },
  active: {
    icon: <PlayCircleFilled style={{ color: '#6C5CE7', fontSize: 18 }} />,
    bg: '#F3F0FF',
    border: '#6C5CE7',
    textColor: '#111827',
    dot: '#6C5CE7',
  },
  pending: {
    icon: <span style={{
      width: 18, height: 18, borderRadius: '50%',
      border: '2px solid #D1D5DB', display: 'inline-block',
    }} />,
    bg: 'transparent',
    border: 'transparent',
    textColor: '#6B7280',
    dot: '#D1D5DB',
  },
  locked: {
    icon: <LockOutlined style={{ color: '#D1D5DB', fontSize: 16 }} />,
    bg: 'transparent',
    border: 'transparent',
    textColor: '#D1D5DB',
    dot: '#E5E7EB',
  },
}

function getTaskStatus(task, currentTaskId, tasks) {
  if (task.status === 'completed') return 'completed'
  if (task.id === currentTaskId) return 'active'

  const idx = tasks.findIndex((t) => t.id === task.id)
  const currentIdx = tasks.findIndex((t) => t.id === currentTaskId)
  const prevCompleted = tasks
    .slice(0, idx)
    .every((t) => t.status === 'completed')

  if (currentTaskId && idx > currentIdx) return prevCompleted ? 'pending' : 'locked'
  if (!currentTaskId && idx === 0) return 'active'
  if (!currentTaskId && idx > 0) {
    const allPrevDone = tasks.slice(0, idx).every((t) => t.status === 'completed')
    return allPrevDone ? 'pending' : 'locked'
  }
  return 'pending'
}

/**
 * Left sidebar — structured learning task directory.
 * Tasks map to the five types: objective, lecture, diagram, quiz, exam.
 */
export default function CourseTaskSidebar({
  tasks = [],
  currentTaskId,
  onSelectTask,
  style,
}) {
  if (!tasks.length) {
    return (
      <div style={{
        width: 240, background: '#FFFFFF', borderRadius: 16,
        padding: 24, border: '1px solid #E5E7EB',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#9CA3AF', fontSize: 13,
        ...style,
      }}>
        暂无学习任务
      </div>
    )
  }

  return (
    <div style={{
      width: 240, minWidth: 240,
      background: '#FFFFFF', borderRadius: 16,
      border: '1px solid #E5E7EB',
      overflow: 'auto',
      display: 'flex', flexDirection: 'column',
      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      ...style,
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px 12px',
        borderBottom: '1px solid #E5E7EB',
        fontSize: 14, fontWeight: 600, color: '#111827',
        display: 'flex', alignItems: 'center', gap: 8,
      }}>
        <UnorderedListOutlined style={{ color: '#6C5CE7' }} />
        学习任务目录
      </div>

      {/* Task List */}
      <div style={{ flex: 1, padding: '8px 12px', overflow: 'auto' }}>
        {tasks.map((task, idx) => {
          const status = getTaskStatus(task, currentTaskId, tasks)
          const st = STATUS_STYLES[status]
          const typeConfig = TASK_TYPES[task.type] || TASK_TYPES['lecture']
          const isClickable = status !== 'locked'

          return (
            <Tooltip
              key={task.id || idx}
              title={status === 'locked' ? '请先完成前置任务' : task.title}
            >
              <button
                onClick={() => isClickable && onSelectTask?.(task)}
                disabled={!isClickable}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  width: '100%',
                  padding: '12px 12px',
                  marginBottom: 4,
                  borderRadius: 12,
                  border: status === 'active' ? `1.5px solid ${st.border}` : '1.5px solid transparent',
                  background: status === 'active' || status === 'completed' ? st.bg : 'transparent',
                  cursor: isClickable ? 'pointer' : 'not-allowed',
                  opacity: status === 'locked' ? 0.45 : 1,
                  transition: 'all 0.2s',
                  textAlign: 'left',
                  fontFamily: 'inherit',
                }}
                onMouseEnter={(e) => {
                  if (isClickable && status !== 'active') {
                    e.currentTarget.style.background = '#F9F7FF'
                  }
                }}
                onMouseLeave={(e) => {
                  if (isClickable && status !== 'active') {
                    e.currentTarget.style.background = 'transparent'
                  }
                }}
              >
                {/* Status indicator */}
                <div style={{ flexShrink: 0, width: 20, display: 'flex', justifyContent: 'center' }}>
                  {st.icon}
                </div>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: 10, color: '#9CA3AF',
                    textTransform: 'uppercase', letterSpacing: 0.5,
                    marginBottom: 2,
                  }}>
                    {typeConfig.label}
                  </div>
                  <div style={{
                    fontSize: 13, fontWeight: status === 'active' ? 600 : 400,
                    color: st.textColor,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {task.title || `任务 ${idx + 1}`}
                  </div>
                </div>

                {/* Estimated time */}
                {task.estimatedMinutes && (
                  <span style={{
                    fontSize: 11, color: '#9CA3AF',
                    flexShrink: 0,
                  }}>
                    {task.estimatedMinutes}min
                  </span>
                )}
              </button>
            </Tooltip>
          )
        })}
      </div>

      {/* Footer — stage summary */}
      <div style={{
        padding: '12px 20px',
        borderTop: '1px solid #E5E7EB',
        fontSize: 12, color: '#6B7280',
      }}>
        {Math.min(tasks.filter((t) => t.status === 'completed').length, tasks.length)} / {tasks.length} 已完成
      </div>
    </div>
  )
}
