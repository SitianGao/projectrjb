import { useState, useCallback } from 'react'
import { Button, Empty, Progress, Space, Tag, Typography, Radio, message, Card } from 'antd'
import {
  AimOutlined, ArrowLeftOutlined, ArrowRightOutlined,
  CheckCircleFilled, ClockCircleOutlined, FileTextOutlined,
  SaveOutlined, LockOutlined, BulbOutlined, EditOutlined,
} from '@ant-design/icons'
import MarkdownRenderer from './MarkdownRenderer'

const { Text, Title, Paragraph } = Typography

const TASK_TYPE_LABELS = {
  goal: '学习目标', document: '核心讲义', video: '视频学习',
  mindmap: '概念图解', exercise: '练习任务', knowledge_check: '知识检查',
  assessment: '阶段测评', project: '项目任务', code: '代码挑战',
}

function GoalContent({ task }) {
  return (
    <div>
      <div style={{ marginBottom: 20, padding: '14px 18px', background: '#F3F0FF', borderRadius: 12 }}>
        <Text strong style={{ color: '#6C5CE7', fontSize: 14 }}><AimOutlined /> 本阶段学习目标</Text>
        <Paragraph style={{ margin: '8px 0 0', fontSize: 13, color: '#374151', lineHeight: 1.8 }}>
          {task.objective || task.description || '完成本阶段学习目标'}
        </Paragraph>
      </div>
      {task.objectives && (
        <ul style={{ color: '#6B7280', fontSize: 13, lineHeight: 2, paddingLeft: 20 }}>
          {Array.isArray(task.objectives) ? task.objectives.map((o, i) => <li key={i}>{o}</li>) : null}
        </ul>
      )}
      {task.estimatedMinutes && (
        <div style={{ marginTop: 12, fontSize: 13, color: '#6B7280' }}>
          <ClockCircleOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />
          预计用时 {task.estimatedMinutes} 分钟
        </div>
      )}
    </div>
  )
}

function DocumentContent({ task }) {
  return task.content ? <MarkdownRenderer content={task.content} compact /> : (
    <Empty description={<span>讲义内容加载中...</span>} image={Empty.PRESENTED_IMAGE_SIMPLE} />
  )
}

function MindmapContent({ task }) {
  return task.content ? <MarkdownRenderer content={task.content} compact /> : (
    <div style={{ textAlign: 'center', padding: 40, color: '#9CA3AF' }}>
      <BulbOutlined style={{ fontSize: 48, marginBottom: 12 }} />
      <div>概念图解数据加载中...</div>
    </div>
  )
}

function ExerciseContent({ task, onAnswer }) {
  const [selected, setSelected] = useState(null)
  const [submitted, setSubmitted] = useState(false)
  const questions = Array.isArray(task.questions) ? task.questions : (task.content ? [{ question: task.content, options: task.options, answer: task.answer }] : [])

  if (!questions.length) {
    return <Empty description="暂无练习题" image={Empty.PRESENTED_IMAGE_SIMPLE} />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {questions.map((q, qi) => {
        const isCorrect = submitted && selected === q.answer
        return (
          <Card key={qi} size="small" style={{ borderRadius: 10, border: '1px solid #E5E7EB' }}>
            <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 10 }}>{qi + 1}. {q.question}</Text>
            {q.options?.length > 0 ? (
              <Radio.Group value={selected} onChange={(e) => !submitted && setSelected(e.target.value)} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {q.options.map((opt, oi) => {
                  const key = typeof opt === 'string' ? String.fromCharCode(65 + oi) : (opt.key || String.fromCharCode(65 + oi))
                  const text = typeof opt === 'string' ? opt : (opt.content || opt.text || '')
                  let st = {}
                  if (submitted && key === q.answer) st = { color: '#22C55E', fontWeight: 'bold' }
                  if (submitted && key === selected && key !== q.answer) st = { color: '#EF4444' }
                  return <Radio key={key} value={key} disabled={submitted} style={st}>{key}. {text}</Radio>
                })}
              </Radio.Group>
            ) : null}
            {submitted && (
              <div style={{ marginTop: 10, padding: '8px 12px', borderRadius: 8, background: isCorrect ? '#F0FDF4' : '#FFF2F0' }}>
                <Text style={{ color: isCorrect ? '#22C55E' : '#EF4444', fontSize: 13 }}>
                  {isCorrect ? '✓ 正确' : `✗ 错误，正确答案：${q.answer}`}
                </Text>
                {q.explanation && <Paragraph style={{ fontSize: 12, color: '#6B7280', margin: '4px 0 0' }}>{q.explanation}</Paragraph>}
              </div>
            )}
            {!submitted && (
              <Button size="small" type="primary" onClick={() => { setSubmitted(true); onAnswer?.(q, selected) }}
                disabled={!selected} style={{ marginTop: 10, borderRadius: 6, background: '#6C5CE7' }}>
                提交答案
              </Button>
            )}
          </Card>
        )
      })}
    </div>
  )
}

function KnowledgeCheckContent({ task }) {
  return <ExerciseContent task={task} />
}

function AssessmentContent({ task }) {
  return (
    <div style={{ textAlign: 'center', padding: 30 }}>
      <EditOutlined style={{ fontSize: 48, color: '#6C5CE7', marginBottom: 16 }} />
      <Title level={4}>阶段测评</Title>
      <Paragraph style={{ color: '#6B7280' }}>题目数量：{task.questionCount || 5} 题 | 预计用时：{task.estimatedMinutes || 20} 分钟 | 通过标准：{task.passThreshold || 70}%</Paragraph>
      <Button type="primary" size="large" style={{ borderRadius: 8, background: '#6C5CE7' }}>
        开始测评
      </Button>
    </div>
  )
}

const CONTENT_MAP = {
  goal: GoalContent, document: DocumentContent, video: DocumentContent,
  mindmap: MindmapContent, exercise: ExerciseContent,
  knowledge_check: KnowledgeCheckContent, assessment: AssessmentContent,
  project: DocumentContent, code: DocumentContent,
}

/**
 * Central content panel — renders different content based on task_type.
 */
export default function LearningContentPanel({
  task, taskIndex, totalTasks, onPrev, onNext, onComplete, onSave, completing, saving, style,
}) {
  if (!task) {
    return (
      <div style={{ flex: 1, background: '#FFFFFF', borderRadius: 16, padding: 48, border: '1px solid #E5E7EB', display: 'flex', alignItems: 'center', justifyContent: 'center', ...style }}>
        <Empty description="请选择一个学习任务开始" />
      </div>
    )
  }

  const isLastTask = taskIndex != null && taskIndex >= totalTasks - 1
  const isCompleted = task.status === 'completed'
  const isLocked = task.status === 'locked'
  const taskType = task.type || 'document'
  const TaskContent = CONTENT_MAP[taskType] || CONTENT_MAP['document']

  if (isLocked) {
    return (
      <div style={{ flex: 1, background: '#FFFFFF', borderRadius: 16, padding: 48, border: '1px solid #E5E7EB', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16, ...style }}>
        <LockOutlined style={{ fontSize: 48, color: '#D1D5DB' }} />
        <Title level={4} style={{ color: '#111827' }}>任务未解锁</Title>
        <Paragraph style={{ color: '#6B7280' }}>请先完成前置任务：{task.prerequisite || '上一任务'}</Paragraph>
        <Button onClick={onPrev} style={{ borderRadius: 8 }}>返回上一任务</Button>
      </div>
    )
  }

  return (
    <div style={{ flex: 1, background: '#FFFFFF', borderRadius: 16, border: '1px solid #E5E7EB', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.04)', ...style }}>
      {/* Header */}
      <div style={{ padding: '20px 28px', borderBottom: '1px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <Tag color="purple" style={{ borderRadius: 6, margin: 0 }}>{taskIndex != null ? `任务 ${taskIndex + 1}` : '当前任务'}</Tag>
            <Tag style={{ borderRadius: 6, margin: 0 }}>{TASK_TYPE_LABELS[taskType] || taskType}</Tag>
            {isCompleted && <Tag color="success" icon={<CheckCircleFilled />} style={{ borderRadius: 6, margin: 0 }}>已完成</Tag>}
          </div>
          <Title level={4} style={{ margin: '4px 0', color: '#111827', fontSize: 20 }}>{task.title || '学习任务'}</Title>
          {task.objective && (
            <Text style={{ fontSize: 14, color: '#6B7280', display: 'flex', alignItems: 'center', gap: 6 }}>
              <AimOutlined style={{ color: '#6C5CE7' }} />{task.objective}
            </Text>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexShrink: 0 }}>
          {task.estimatedMinutes && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: '#6B7280', padding: '6px 12px', background: '#F9F7FF', borderRadius: 8 }}>
              <ClockCircleOutlined style={{ color: '#6C5CE7' }} />{task.estimatedMinutes} 分钟
            </div>
          )}
        </div>
      </div>

      {/* Content body */}
      <div style={{ flex: 1, overflow: 'auto', padding: '20px 28px' }}>
        <TaskContent task={task} />
      </div>

      {/* Progress bar */}
      {task.progress != null && (
        <div style={{ padding: '0 28px' }}>
          <Progress percent={task.progress} size="small" strokeColor="#6C5CE7" />
        </div>
      )}

      {/* Footer — save + complete + navigation */}
      <div style={{ padding: '16px 28px', borderTop: '1px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#FAFAFC' }}>
        <Button icon={<ArrowLeftOutlined />} onClick={onPrev} disabled={taskIndex == null || taskIndex <= 0} style={{ borderRadius: 10 }}>上一任务</Button>
        <Space size={12}>
          {!isCompleted && (
            <>
              <Button icon={<SaveOutlined />} onClick={() => onSave?.(task)} loading={saving} style={{ borderRadius: 10 }}>保存进度</Button>
              <Button type="primary" icon={<CheckCircleFilled />}
                onClick={() => onComplete?.(task)} loading={completing}
                style={{ borderRadius: 10, background: '#6C5CE7', borderColor: '#6C5CE7', boxShadow: '0 2px 6px rgba(108,92,231,0.3)' }}>
                {isLastTask ? '完成并进入阶段测评' : '完成并进入下一任务'}
              </Button>
            </>
          )}
          {isCompleted && !isLastTask && (
            <Button icon={<ArrowRightOutlined />} onClick={onNext} style={{ borderRadius: 10 }}>下一任务</Button>
          )}
        </Space>
      </div>
    </div>
  )
}
