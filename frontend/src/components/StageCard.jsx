import { useState } from 'react'
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
  completed: { label: '已完成', color: '#22C55E', bg: '#F0FDF4', icon: <CheckCircleFilled /> },
  current: { label: '进行中', color: '#6C5CE7', bg: '#F3F0FF', icon: <PlayCircleFilled /> },
  locked: { label: '未解锁', color: '#9CA3AF', bg: '#F9FAFB', icon: <LockFilled /> },
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
          border: status === 'current' ? '1.5px solid #6C5CE7' : '1px solid #E5E7EB',
          background: '#FFFFFF',
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
            <Text strong style={{ fontSize: 15, color: '#111827' }}>
              阶段{stageIndex}：{stage?.title || '未命名'}
            </Text>
            <Tag color={status === 'current' ? 'purple' : status === 'completed' ? 'success' : 'default'} style={{ borderRadius: 6 }}>
              {cfg.label}
            </Tag>
          </Space>
          {!isLocked && (
            <CaretRightOutlined
              style={{
                color: '#9CA3AF', fontSize: 12,
                transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s',
              }}
            />
          )}
        </div>

        {/* Row 2: tasks, days, resources, mastery */}
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginTop: 10 }}>
          <span style={{ fontSize: 13, color: '#6B7280' }}>
            任务 {completed}/{tasks.length}
          </span>
          <span style={{ fontSize: 13, color: '#6B7280' }}>
            预计 {days} 天
          </span>
          <span style={{ fontSize: 13, color: '#6B7280' }}>
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
          <div style={{ marginTop: 14, borderTop: '1px solid #F3F4F6', paddingTop: 14 }}>
            {/* Learning objectives */}
            {objectives.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <Text strong style={{ fontSize: 13, color: '#111827' }}>
                  <AimOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />
                  学习目标
                </Text>
                <Paragraph style={{ margin: '6px 0 0', fontSize: 13, color: '#6B7280', lineHeight: 1.7 }}>
                  {objectives.join('；')}
                </Paragraph>
              </div>
            )}

            {/* Knowledge tags */}
            {topics.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <Text strong style={{ fontSize: 13, color: '#111827', display: 'block', marginBottom: 8 }}>
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

            {/* Lock condition */}
            {isLocked && (
              <Text style={{ fontSize: 12, color: '#9CA3AF', display: 'block', marginBottom: 12 }}>
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
