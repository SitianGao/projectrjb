import { Button, Drawer, Progress, Space, Tag, Typography } from 'antd'
import {
  AimOutlined, BookOutlined, ClockCircleOutlined, FileTextOutlined,
  PlayCircleFilled, TagsOutlined, UnorderedListOutlined,
} from '@ant-design/icons'
import MarkdownRenderer from './MarkdownRenderer'
import { normalizeStringList, normalizeTasks } from '../utils/stageUtils'
import { safeProgress, dedupeResources } from '../utils/safeClamp'

const { Text, Paragraph } = Typography

/**
 * Side drawer showing full stage details: objectives, topics,
 * task list, matched resources, and path reasoning.
 */
export default function StageDetailDrawer({
  stage,
  resources = [],
  visible,
  onClose,
  onContinue,
  onResourceClick,
}) {
  if (!stage) return null

  const tasks = normalizeTasks(stage?.tasks)
  const completed = tasks.filter((t) => t.status === 'completed').length
  const { percent } = safeProgress(completed, tasks.length)
  const objectives = normalizeStringList(stage?.objectives)
  const topics = normalizeStringList(stage?.topics)
  const uniqueResources = dedupeResources(resources)

  return (
    <Drawer
      title={
        <Space>
          <Text strong style={{ fontSize: 16 }}>{stage.title}</Text>
          <Tag color="purple">阶段{stage.stage_id}</Tag>
        </Space>
      }
      open={visible}
      onClose={onClose}
      width={520}
      styles={{ body: { padding: '20px 24px' } }}
    >
      {/* Progress */}
      {tasks.length > 0 && (
        <div style={{ marginBottom: 18 }}>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>任务进度</Text>
          <Progress percent={percent} strokeColor="#6C5CE7" />
          <Text type="secondary" style={{ fontSize: 12 }}>{completed} / {tasks.length} 已完成</Text>
        </div>
      )}

      {/* Objectives */}
      {objectives.length > 0 && (
        <div style={{ marginBottom: 18 }}>
          <Text strong style={{ fontSize: 13, color: 'var(--text-primary)', display: 'block', marginBottom: 6 }}>
            <AimOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />学习目标
          </Text>
          <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.8 }}>
            {objectives.map((obj, i) => <li key={i}>{obj}</li>)}
          </ul>
        </div>
      )}

      {/* Knowledge points */}
      {topics.length > 0 && (
        <div style={{ marginBottom: 18 }}>
          <Text strong style={{ fontSize: 13, color: 'var(--text-primary)', display: 'block', marginBottom: 6 }}>
            <TagsOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />核心知识点
          </Text>
          <Space size={4} wrap>
            {topics.map((t) => <Tag key={t} color="purple" style={{ borderRadius: 6 }}>{t}</Tag>)}
          </Space>
        </div>
      )}

      {/* Task list */}
      {tasks.length > 0 && (
        <div style={{ marginBottom: 18 }}>
          <Text strong style={{ fontSize: 13, color: 'var(--text-primary)', display: 'block', marginBottom: 6 }}>
            <UnorderedListOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />学习任务
          </Text>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {tasks.map((task) => (
              <div key={task.task_id} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '6px 10px', borderRadius: 6,
                background: task.status === 'completed' ? 'var(--stage-completed-bg)' : 'var(--surface-secondary)',
                fontSize: 13,
              }}>
                <span style={{ flex: 1, color: 'var(--text-primary)' }}>{task.description}</span>
                {task.estimated_hours && (
                  <Text type="secondary" style={{ fontSize: 11 }}><ClockCircleOutlined /> {task.estimated_hours}h</Text>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Matched resources */}
      {uniqueResources.length > 0 && (
        <div style={{ marginBottom: 18 }}>
          <Text strong style={{ fontSize: 13, color: 'var(--text-primary)', display: 'block', marginBottom: 6 }}>
            <FileTextOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />阶段资源（{uniqueResources.length} 项）
          </Text>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {uniqueResources.map((res) => (
              <div
                key={res.id}
                onClick={() => onResourceClick?.(res)}
                style={{
                  padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)',
                  cursor: 'pointer', fontSize: 13, color: 'var(--text-primary)',
                  minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis',
                }}
              >
                <BookOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />
                {res.title}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unlock condition for locked stages */}
      {stage.stage_id > 1 && (
        <Paragraph style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 18, padding: '10px 14px', background: 'var(--surface-secondary)', borderRadius: 8 }}>
          解锁条件：完成阶段{stage.stage_id - 1}测评且正确率达到 70%
        </Paragraph>
      )}

      {/* Action */}
      <Button
        type="primary"
        block
        icon={<PlayCircleFilled />}
        onClick={() => onContinue?.(stage)}
        style={{ borderRadius: 8, background: '#6C5CE7', borderColor: '#6C5CE7' }}
      >
        进入该阶段学习
      </Button>
    </Drawer>
  )
}
