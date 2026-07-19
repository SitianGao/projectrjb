import { Button, Card, Progress, Space, Tag, Typography } from 'antd'
import {
  CheckCircleFilled,
  LockFilled,
  PlayCircleFilled,
  RightOutlined,
  CaretRightOutlined,
  AimOutlined,
} from '@ant-design/icons'
import { safeProgress } from '../utils/safeClamp'
import { normalizeStringList, normalizeTasks } from '../utils/stageUtils'

const { Text, Paragraph } = Typography

const STATUS_MAP = {
  completed: { label: '已完成', color: '#22C55E', bg: 'var(--stage-completed-bg)', icon: <CheckCircleFilled /> },
  current: { label: '进行中', color: '#6C5CE7', bg: 'var(--tint-primary)', icon: <PlayCircleFilled /> },
  locked: { label: '未解锁', color: 'var(--text-muted)', bg: 'var(--surface-secondary)', icon: <LockFilled /> },
}

/**
 * Single stage card showing: status, tasks, days, resources, objectives, knowledge tags.
 * Current stage is expanded by default.
 */
export default function StageCard({
  stage,
  status,
  stageIndex,
  resources = [],
  onContinue,
  onViewDetail,
  onTaskOpen,
  expanded = false,
  onToggle,
}) {
  const cfg = STATUS_MAP[status] || STATUS_MAP.locked
  const tasks = normalizeTasks(stage?.tasks)
  const completed = tasks.filter((t) => t.status === 'completed').length
  const { percent } = safeProgress(completed, tasks.length)
  const objectives = normalizeStringList(stage?.objectives)
  const topics = normalizeStringList(stage?.topics).slice(0, 4)
  const extraTopics = Math.max(0, normalizeStringList(stage?.topics).length - 4)
  const days = stage?.estimated_days || Math.max(1, Math.round(tasks.reduce((s, t) => s + (t.estimated_hours || 0.5), 0) / 2))
  const isLocked = status === 'locked'

  return (
    <div style={{ marginBottom: 12 }}>
      <Card
        size="small"
        style={{
          borderRadius: 12,
          border: status === 'current' ? '1.5px solid #6C5CE7' : '1px solid var(--border)',
          background: 'var(--bg-card)',
          opacity: isLocked ? 0.6 : 1,
          cursor: isLocked ? 'default' : 'pointer',
          minWidth: 0,
        }}
        onClick={() => !isLocked && onToggle?.(stage)}
      >
        {/* Row 1: stage number, name, status tag */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
          <Space size={8}>
            <span style={{ color: cfg.color, fontSize: 18 }}>{cfg.icon}</span>
            <Text strong style={{ fontSize: 15, color: 'var(--text-primary)' }}>
              阶段{stageIndex}：{stage?.title || '未命名'}
            </Text>
            <Tag color={status === 'current' ? 'purple' : status === 'completed' ? 'success' : 'default'} style={{ borderRadius: 6 }}>
              {cfg.label}
            </Tag>
          </Space>
          {!isLocked && (
            <CaretRightOutlined
              style={{
                color: 'var(--text-muted)', fontSize: 12,
                transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s',
              }}
            />
          )}
        </div>

        {/* Row 2: tasks, days, resources, mastery */}
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginTop: 10 }}>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            任务 {completed}/{tasks.length}
          </span>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            预计 {days} 天
          </span>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            资源 {resources.length} 项
          </span>
          {tasks.length > 0 && (
            <Progress
              percent={percent}
              size="small"
              style={{ width: 100, margin: 0 }}
              strokeColor="#6C5CE7"
            />
          )}
        </div>

        {/* Expanded content */}
        {expanded && !isLocked && (
          <div style={{ marginTop: 14, borderTop: '1px solid var(--border)', paddingTop: 14 }}>
            {/* Learning objectives */}
            {objectives.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <Text strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>
                  <AimOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />
                  学习目标
                </Text>
                <Paragraph style={{ margin: '6px 0 0', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                  {objectives.join('；')}
                </Paragraph>
              </div>
            )}

            {/* Adaptation reason — "为什么为你这样安排" */}
            {stage?.adaptation_reason && (
              <div style={{
                marginBottom: 12, padding: '10px 14px',
                background: 'linear-gradient(135deg, #FFF7ED, #FFF1F2)',
                borderRadius: 10, border: '1px solid #FED7AA',
              }}>
                <Text strong style={{ fontSize: 12, color: '#EA580C', display: 'block', marginBottom: 4 }}>
                  💡 为什么为你这样安排
                </Text>
                <Text style={{ fontSize: 12, color: '#9A3412', lineHeight: 1.6 }}>
                  {stage.adaptation_reason}
                </Text>
              </div>
            )}

            {/* Knowledge tags */}
            {topics.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <Text strong style={{ fontSize: 13, color: 'var(--text-primary)', display: 'block', marginBottom: 8 }}>
                  核心知识点
                </Text>
                <Space size={4} wrap>
                  {topics.map((t) => (
                    <Tag key={t} color="purple" style={{ borderRadius: 6, fontSize: 12 }}>{t}</Tag>
                  ))}
                  {extraTopics > 0 && <Tag style={{ borderRadius: 6, fontSize: 12 }}>+{extraTopics}</Tag>}
                </Space>
              </div>
            )}

            {tasks.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <Text strong style={{ fontSize: 13, color: 'var(--text-primary)', display: 'block', marginBottom: 8 }}>
                  学习任务
                </Text>
                <div style={{ display: 'grid', gap: 6 }}>
                  {tasks.map((task) => {
                    const locked = task.status === 'locked'
                    const triggerSource = task.trigger_source || task.triggerSource
                    const isDynamic = Boolean(
                      task.dynamic_source
                      || task.dynamicSource
                      || ['evaluation', 'path_adjustment'].includes(triggerSource),
                    )
                    const adjustmentReason = task.adjustment_reason
                      || task.adjustmentReason
                      || (isDynamic ? task.description : '')
                    const contentReady = Boolean(
                      task.resource_id
                      || task.content_preparation_status === 'ready'
                      || task.contentPreparationStatus === 'ready',
                    )
                    return (
                      <button
                        key={task.task_id || task.id}
                        type="button"
                        disabled={locked}
                        onClick={(event) => {
                          event.stopPropagation()
                          onTaskOpen?.(task)
                        }}
                        title={locked ? (task.unlock_condition || task.unlockCondition || '请先完成前置任务') : ''}
                        style={{
                          width: '100%',
                          minHeight: 38,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: 12,
                          padding: '8px 10px',
                          border: '1px solid var(--border)',
                          borderRadius: 8,
                          background: task.status === 'active' ? 'var(--tint-primary)' : 'var(--bg-card)',
                          color: locked ? 'var(--text-muted)' : 'var(--text-primary)',
                          cursor: locked ? 'not-allowed' : 'pointer',
                          textAlign: 'left',
                        }}
                      >
                        <span style={{ minWidth: 0, display: 'grid', gap: 4 }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                            {task.title || task.description || '学习任务'}
                            {isDynamic && (
                              <Tag color="purple" style={{ fontSize: 10, borderRadius: 6, margin: 0, lineHeight: '16px' }}>
                                AI 学习诊断后新增
                              </Tag>
                            )}
                          </span>
                          {isDynamic && (
                            <span style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                              {adjustmentReason && (
                                <Text type="secondary" style={{ fontSize: 11 }}>
                                  调整原因：{adjustmentReason}
                                </Text>
                              )}
                              <Tag
                                color={contentReady ? 'success' : 'processing'}
                                style={{ fontSize: 10, borderRadius: 6, margin: 0, lineHeight: '16px' }}
                              >
                                {contentReady ? '内容已准备' : '内容准备中'}
                              </Tag>
                            </span>
                          )}
                        </span>
                        {locked ? <LockFilled /> : <RightOutlined />}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Lock condition */}
            {isLocked && (
              <Text style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 12 }}>
                完成阶段{stageIndex - 1}测评且正确率达到 70% 后解锁
              </Text>
            )}

            {/* Action buttons */}
            {!isLocked && (
              <Space size={8}>
                <Button
                  type="primary"
                  size="small"
                  icon={<PlayCircleFilled />}
                  onClick={(e) => { e.stopPropagation(); onContinue?.() }}
                  style={{ borderRadius: 8, background: '#6C5CE7', borderColor: '#6C5CE7' }}
                >
                  继续学习
                </Button>
                <Button
                  size="small"
                  icon={<RightOutlined />}
                  onClick={(e) => { e.stopPropagation(); onViewDetail?.(stage) }}
                  style={{ borderRadius: 8 }}
                >
                  查看阶段详情
                </Button>
              </Space>
            )}
          </div>
        )}
      </Card>
    </div>
  )
}
