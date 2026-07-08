import { useState } from 'react'
import { Typography, Input, Select, Button, Empty, Row, Col, message, Modal } from 'antd'
import {
  SearchOutlined, ThunderboltOutlined, FileTextOutlined,
  EditOutlined, CodeOutlined, ReloadOutlined,
} from '@ant-design/icons'
import ResourceCard from '../components/ResourceCard'
import MarkdownRenderer from '../components/MarkdownRenderer'
import ProgressBar from '../components/ProgressBar'
import { useTaskStatus } from '../hooks/useTaskStatus'
import { generateResources, getTaskStatus } from '../api/resource'
const { Text } = Typography

const DIFFICULTY_OPTIONS = [
  { value: 'beginner', label: '初级' },
  { value: 'intermediate', label: '中级' },
  { value: 'advanced', label: '高级' },
]

const DIFFICULTY_COLORS = {
  beginner: '#22c55e',
  intermediate: '#f59e0b',
  advanced: '#ef4444',
}

const TYPE_OPTIONS = [
  { value: 'document', label: '文档' },
  { value: 'exercise', label: '练习题' },
  { value: 'code', label: '代码' },
]

const TYPE_ICONS = {
  document: <FileTextOutlined />,
  exercise: <EditOutlined />,
  code: <CodeOutlined />,
}

/**
 * 学习资源页
 * - 接入 useTaskStatus 轮询异步任务进度
 * - 生成中显示 ProgressBar + 阶段文案，按钮禁用
 * - 完成后自动替换为资源卡片
 * - 失败时显示重试按钮
 */
export default function ResourcePage() {
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('intermediate')
  const [selectedTypes, setSelectedTypes] = useState(['document', 'exercise', 'code'])
  const [detailResource, setDetailResource] = useState(null)

  // 异步任务轮询
  const {
    status, result, error,
    progress, taskMessage,
    startPolling, reset,
  } = useTaskStatus(async (taskId) => {
    const data = await getTaskStatus(taskId)
    return {
      status: data.status === 'done' ? 'completed' : data.status,
      result: data.result,
      error: data.error,
      progress: data.progress ?? 0,
      message: data.message ?? '',
    }
  })

  const isRunning = status === 'pending' || status === 'running'
  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'

  /** 点击生成 — 调后端接口启动异步任务 */
  async function handleGenerate() {
    if (!topic.trim()) {
      message.warning('请输入学习主题')
      return
    }
    if (selectedTypes.length === 0) {
      message.warning('请至少选择一种资源类型')
      return
    }

    try {
      const diffLabel = DIFFICULTY_OPTIONS.find((d) => d.value === difficulty)?.label || '中级'
      const data = await generateResources({
        student_id: 'demo-student-01',
        topic: topic.trim(),
        types: selectedTypes,
        difficulty: diffLabel,
      })

      if (data.task_id) {
        startPolling(data.task_id)
      } else {
        message.error('未获取到任务 ID')
      }
    } catch (err) {
      message.error('生成请求失败: ' + (err.message || '未知错误'))
    }
  }

  /** 失败后重试 */
  function handleRetry() {
    reset()
    handleGenerate()
  }

  /** 从 result 中提取资源列表 */
  const resultResources = (() => {
    if (!isCompleted || !result) return []
    if (Array.isArray(result)) return result
    return result.items || result.resources || []
  })()

  /** 根据进度百分比推演步骤状态 */
  function buildSteps() {
    const phaseLabels = [
      { key: 'understand', label: '了解主题' },
      { key: 'prepare', label: '准备资料' },
      { key: 'polish', label: '排版整理' },
    ]
    return phaseLabels.map((phase, i) => {
      const threshold = (i + 1) / phaseLabels.length * 100
      if (progress >= threshold || isCompleted) return { ...phase, status: 'finish' }
      if (progress >= i / phaseLabels.length * 100 && isRunning) return { ...phase, status: 'process' }
      return { ...phase, status: 'wait' }
    })
  }

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: 24 }}>
      {/* ── 参数输入区 ── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        marginBottom: 24,
      }}>
        <Input
          placeholder="输入学习主题，如：二次函数"
          prefix={<SearchOutlined style={{ color: '#8b5cf6' }} />}
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onPressEnter={handleGenerate}
          style={{ flex: 1, minWidth: 180, borderRadius: 8 }}
          allowClear
          disabled={isRunning}
        />
        <Select
          value={difficulty}
          onChange={setDifficulty}
          style={{ width: 100, borderRadius: 8 }}
          popupMatchSelectWidth={false}
          disabled={isRunning}
        >
          {DIFFICULTY_OPTIONS.map((opt) => (
            <Select.Option key={opt.value} value={opt.value}
              label={
                <span style={{ color: DIFFICULTY_COLORS[opt.value], fontWeight: 500 }}>
                  {opt.label}
                </span>
              }
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: DIFFICULTY_COLORS[opt.value],
                  flexShrink: 0,
                }} />
                <span>{opt.label}</span>
              </span>
            </Select.Option>
          ))}
        </Select>
        <Select
          mode="multiple"
          value={selectedTypes}
          onChange={setSelectedTypes}
          options={TYPE_OPTIONS}
          style={{ width: 130, borderRadius: 8 }}
          placeholder="资源类型"
          disabled={isRunning}
          optionRender={(option) => (
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: '#8b5cf6' }}>{TYPE_ICONS[option.value]}</span>
              <span>{option.label}</span>
            </span>
          )}
          tagRender={({ value, closable, onClose }) => (
            <span
              style={{ display: 'inline-flex', alignItems: 'center', color: '#8b5cf6', marginRight: 2 }}
              onMouseDown={(e) => { e.preventDefault(); e.stopPropagation() }}
            >
              {TYPE_ICONS[value]}
            </span>
          )}
        />
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          onClick={handleGenerate}
          loading={isRunning}
          disabled={isRunning}
          style={{
            background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
            border: 'none',
            borderRadius: 8,
            minWidth: 120,
            flexShrink: 0,
          }}
        >
          {isRunning ? '生成中...' : '生成资源'}
        </Button>
      </div>

      {/* ── 生成进度区 ── */}
      {isRunning && (
        <div style={{
          background: 'var(--bg-card)', borderRadius: 12, padding: '24px 32px',
          border: '1px solid var(--border)',
        }}>
          <ProgressBar
            status={status}
            percent={progress}
            steps={buildSteps()}
            message={taskMessage || '准备中…'}
            error={error}
          />
        </div>
      )}

      {/* ── 失败区 ── */}
      {isFailed && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: 320,
          background: 'var(--surface-secondary)', borderRadius: 12, gap: 16,
        }}>
          <ProgressBar
            status="failed"
            percent={progress}
            message={taskMessage || '生成失败'}
            error={error}
          />
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={handleRetry}
            style={{ borderRadius: 8 }}
          >
            重新生成
          </Button>
        </div>
      )}

      {/* ── 结果区 ── */}
      {!isRunning && !isFailed && (
        isCompleted && resultResources.length > 0 ? (
          <Row gutter={[16, 16]}>
            {resultResources.map((r) => (
              <Col key={r.id} xs={24} md={8}>
                <ResourceCard resource={r} onClick={(res) => setDetailResource(res)} />
              </Col>
            ))}
          </Row>
        ) : isCompleted && resultResources.length === 0 ? (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            minHeight: 320, background: 'var(--surface-secondary)', borderRadius: 12,
          }}>
            <Empty description={<Text type="secondary">没有匹配的资源</Text>} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          </div>
        ) : (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            minHeight: 320, background: 'var(--surface-secondary)', borderRadius: 12,
          }}>
            <Empty description={<Text type="secondary">暂无资源，先输入主题生成</Text>} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          </div>
        )
      )}

      {/* ── 详情弹窗 ── */}
      <Modal
        title={detailResource?.title}
        open={!!detailResource}
        onCancel={() => setDetailResource(null)}
        footer={null}
        width={960}
        style={{ top: 40 }}
        styles={{ body: { maxHeight: '80vh', overflow: 'auto', padding: '24px 32px' } }}
      >
        {detailResource && <MarkdownRenderer content={detailResource.content} />}
      </Modal>
    </div>
  )
}
