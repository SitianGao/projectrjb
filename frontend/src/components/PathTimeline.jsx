import { useState } from 'react'
import { Card, Tag, Typography, Progress, Collapse, Tooltip, Space, List } from 'antd'
import {
  CheckCircleFilled,
  PlayCircleFilled,
  ClockCircleFilled,
  LockFilled,
  CaretRightOutlined,
  BookOutlined,
  StarFilled,
  FlagFilled,
  AimOutlined,
  TagsOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons'
import { SKILL_TAGS, RESOURCE_TYPES } from '../mock/learningPathData'
import { useTheme } from '../contexts/ThemeContext'

const { Text, Title, Paragraph } = Typography

// 任务类型图标映射
const TASK_TYPE_ICONS = {
  study: '📖',
  exercise: '✏️',
  quiz: '📝',
  project: '🔨',
  review: '🔁',
}

// 难度颜色映射
const DIFFICULTY_COLORS = {
  '初级': 'green',
  '中级': 'blue',
  '高级': 'orange',
  '专家': 'red',
}

// 阶段状态配置
const statusConfig = {
  completed: { icon: CheckCircleFilled, color: '#52c41a', bg: '#f6ffed', label: '已完成', dot: '#52c41a' },
  in_progress: { icon: PlayCircleFilled, color: '#1677ff', bg: '#e6f4ff', label: '进行中', dot: '#1677ff', pulse: true },
  pending: { icon: ClockCircleFilled, color: '#d9d9d9', bg: '#fafafa', label: '待开始', dot: '#bfbfbf' },
  locked: { icon: LockFilled, color: '#d9d9d9', bg: '#f5f5f5', label: '未解锁', dot: '#d9d9d9' },
}

/**
 * 学习路径时间线
 *
 * 支持两种数据格式：
 * - stages（新版）：[{ stage_id, title, description, objectives, topics, tasks }]
 * - nodes（旧版）：[{ id, title, description, status, duration, skillTags, resources }]
 *
 * @param {Array}  props.stages         - 新版阶段数组
 * @param {Array}  props.nodes          - 旧版节点数组（兼容）
 * @param {number} props.overallProgress - 整体进度 0-100
 * @param {string} props.title          - 路径标题
 * @param {boolean} props.loading       - 加载状态
 * @param {Function} props.onStageClick - 阶段点击回调
 * @param {Function} props.onNodeClick  - 节点点击回调（旧版兼容）
 */
export default function PathTimeline({
  stages,
  nodes,
  overallProgress = 0,
  title = '',
  loading = false,
  onStageClick,
  onNodeClick,
}) {
  const [expandedId, setExpandedId] = useState(null)
  const { resolved } = useTheme()
  const isDark = resolved === 'dark'

  // 深色模式下的阶段卡片背景
  const darkBgMap = {
    completed: 'rgba(82,196,26,0.06)',
    in_progress: 'rgba(22,119,255,0.06)',
    pending: 'rgba(255,255,255,0.02)',
    locked: 'rgba(255,255,255,0.015)',
  }

  // 统一数据源：优先使用 stages
  const items = stages || nodes || []
  const isStageFormat = !!stages

  if (loading) {
    return <Card loading style={{ minHeight: 200 }} />
  }

  if (!items.length) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 48 }}>
          <BookOutlined style={{ fontSize: 40, color: 'var(--text-muted)' }} />
          <Paragraph type="secondary" style={{ marginTop: 16 }}>暂无学习路径，点击上方按钮生成</Paragraph>
        </div>
      </Card>
    )
  }

  // 计算进度：stage 模式下根据已完成 task 数估算
  let progress = overallProgress
  if (!overallProgress && isStageFormat) {
    const allTasks = items.reduce((sum, s) => sum + (s.tasks?.length || 0), 0)
    const completedTasks = items.reduce(
      (sum, s) => sum + (s.tasks?.filter(t => t.status === 'completed')?.length || 0),
      0,
    )
    progress = allTasks > 0 ? Math.round((completedTasks / allTasks) * 100) : 0
  } else if (!overallProgress) {
    const completedCount = items.filter(n => n.status === 'completed').length
    progress = Math.round((completedCount / items.length) * 100)
  }

  return (
    <div className="path-timeline">
      {/* 路径标题卡片 */}
      {title && (
        <Card className="path-header-card" style={{ marginBottom: 0, borderRadius: '12px 12px 0 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space size={12}>
              <div style={{
                width: 44, height: 44, borderRadius: 12,
                background: 'linear-gradient(135deg, #1677ff 0%, #722ed1 100%)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <StarFilled style={{ fontSize: 22, color: '#fff' }} />
              </div>
              <div>
                <Title level={4} style={{ margin: 0 }}>{title}</Title>
                <Text type="secondary">
                  {items.length} 个{isStageFormat ? '阶段' : '节点'} · 进度 {progress}%
                </Text>
              </div>
            </Space>
            <Progress
              type="circle"
              percent={progress}
              size={52}
              strokeColor={{ '0%': '#1677ff', '100%': '#52c41a' }}
            />
          </div>
        </Card>
      )}

      {/* 时间线轨道 */}
      <div className="timeline-track">
        {items.map((item, idx) => {
          const itemId = isStageFormat ? item.stage_id : item.id
          const isLast = idx === items.length - 1

          if (isStageFormat) {
            return renderStageItem(item, idx, itemId, isLast)
          }
          return renderNodeItem(item, idx, itemId, isLast)
        })}
      </div>
    </div>
  )

  // ─── 新版 Stage 渲染 ────────────────────────────────────────────
  function renderStageItem(stage, idx, itemId, isLast) {
    // 阶段状态推断：第一个默认 in_progress，其余 pending
    const stageStatus = stage.status || (idx === 0 ? 'in_progress' : idx === 1 ? 'pending' : 'locked')
    const cfg = statusConfig[stageStatus] || statusConfig.pending
    const Icon = cfg.icon
    const isActive = stageStatus === 'in_progress'
    const isExpanded = expandedId === itemId
    const completedTasks = stage.tasks?.filter(t => t.status === 'completed')?.length || 0
    const totalTasks = stage.tasks?.length || 0

    return (
      <div key={itemId} className="timeline-node-wrapper">
        <div className="timeline-row">
          {/* 左侧：指示器 */}
          <div className="timeline-indicator">
            <div
              className={`timeline-dot ${isActive ? 'pulse' : ''}`}
              style={{
                background: cfg.dot,
                boxShadow: isActive ? `0 0 0 4px ${cfg.color}30` : 'none',
              }}
            >
              <Icon style={{ fontSize: 14, color: stageStatus === 'pending' || stageStatus === 'locked' ? 'var(--text-muted)' : '#fff' }} />
            </div>
            {!isLast && (
              <div className="timeline-line" style={{ background: stageStatus === 'completed' ? '#52c41a' : 'var(--border)' }} />
            )}
          </div>

          {/* 右侧：内容卡片 */}
          <div
            className={`timeline-card ${isActive ? 'active' : ''} ${stageStatus === 'locked' ? 'locked' : ''}`}
            onClick={() => {
              if (stageStatus !== 'locked') {
                setExpandedId(isExpanded ? null : itemId)
                onStageClick?.(stage)
              }
            }}
            style={{
              background: isDark ? darkBgMap[stageStatus] : cfg.bg,
              borderColor: isActive ? cfg.color : 'transparent',
              cursor: stageStatus === 'locked' ? 'default' : 'pointer',
              opacity: stageStatus === 'locked' ? 0.6 : 1,
            }}
          >
            {/* 阶段头部 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                <Space size={8}>
                  <FlagFilled style={{ color: isActive ? '#1677ff' : 'var(--text-muted)' }} />
                  <Text strong style={{ fontSize: 15, color: stageStatus === 'locked' ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                    第{stage.stage_id}阶段：{stage.title}
                  </Text>
                  <Tag color={cfg.color === '#d9d9d9' ? 'default' : cfg.color}>{cfg.label}</Tag>
                </Space>
                <Paragraph type="secondary" style={{ margin: '6px 0 0', fontSize: 13 }}>
                  {stage.description}
                </Paragraph>
              </div>

              <Space size={12} style={{ flexShrink: 0, marginLeft: 16 }}>
                {totalTasks > 0 && (
                  <Tooltip title="任务进度">
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      📋 {completedTasks}/{totalTasks}
                    </Text>
                  </Tooltip>
                )}
                {stageStatus !== 'locked' && (
                  <CaretRightOutlined
                    style={{
                      fontSize: 12, color: 'var(--text-muted)',
                      transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                      transition: 'transform 0.2s',
                    }}
                  />
                )}
              </Space>
            </div>

            {/* 学习目标 + 知识点标签 */}
            <div style={{ marginTop: 10 }}>
              <Space size={4} wrap>
                {stage.objectives?.map((obj, oi) => (
                  <Tag key={`obj-${oi}`} icon={<AimOutlined />} color="blue" style={{ fontSize: 11, lineHeight: '18px' }}>
                    {obj}
                  </Tag>
                ))}
                {stage.topics?.map((topic, ti) => (
                  <Tag key={`topic-${ti}`} icon={<TagsOutlined />} color="purple" style={{ fontSize: 11, lineHeight: '18px' }}>
                    {topic}
                  </Tag>
                ))}
              </Space>
            </div>

            {/* 展开：任务列表 */}
            {isExpanded && stage.tasks && (
              <div className="timeline-resources" style={{ marginTop: 14 }}>
                <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
                  <UnorderedListOutlined /> 学习任务（{stage.tasks.length} 项）
                </Text>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {stage.tasks.map((task) => {
                    const diffColor = DIFFICULTY_COLORS[task.difficulty] || 'default'
                    return (
                      <div
                        key={task.task_id}
                        className="resource-item"
                        style={{
                          display: 'flex', alignItems: 'center', gap: 8,
                          padding: '6px 10px', borderRadius: 6,
                          background: 'var(--surface-secondary)', border: '1px solid var(--border)',
                          fontSize: 13,
                        }}
                      >
                        <span>{TASK_TYPE_ICONS[task.type] || '📌'}</span>
                        <span style={{ flex: 1 }}>{task.description}</span>
                        <Tag color={diffColor} style={{ fontSize: 10, lineHeight: '16px' }}>{task.difficulty}</Tag>
                        {task.estimated_days != null && (
                          <Text type="secondary" style={{ fontSize: 11 }}>⏱ {task.estimated_days}天</Text>
                        )}
                        {task.prerequisites?.length > 0 && (
                          <Tooltip title={`前置：${task.prerequisites.join(', ')}`}>
                            <Text type="secondary" style={{ fontSize: 10 }}>🔗</Text>
                          </Tooltip>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // ─── 旧版 Node 渲染（兼容）─────────────────────────────────────
  function renderNodeItem(node, idx, itemId, isLast) {
    const cfg = statusConfig[node.status] || statusConfig.pending
    const Icon = cfg.icon
    const isActive = node.status === 'in_progress'
    const isExpanded = expandedId === itemId

    return (
      <div key={itemId} className="timeline-node-wrapper">
        <div className="timeline-row">
          {/* 左侧：指示器 */}
          <div className="timeline-indicator">
            <div
              className={`timeline-dot ${isActive ? 'pulse' : ''}`}
              style={{
                background: cfg.dot,
                boxShadow: isActive ? `0 0 0 4px ${cfg.color}30` : 'none',
              }}
            >
              <Icon style={{ fontSize: 14, color: node.status === 'pending' || node.status === 'locked' ? 'var(--text-muted)' : '#fff' }} />
            </div>
            {!isLast && (
              <div className="timeline-line" style={{ background: node.status === 'completed' ? '#52c41a' : 'var(--border)' }} />
            )}
          </div>

          {/* 右侧：内容卡片 */}
          <div
            className={`timeline-card ${isActive ? 'active' : ''} ${node.status === 'locked' ? 'locked' : ''}`}
            onClick={() => {
              if (node.status !== 'locked') {
                setExpandedId(isExpanded ? null : itemId)
                onNodeClick?.(node)
              }
            }}
            style={{
              background: isDark ? darkBgMap[node.status] : cfg.bg,
              borderColor: isActive ? cfg.color : 'transparent',
              cursor: node.status === 'locked' ? 'default' : 'pointer',
              opacity: node.status === 'locked' ? 0.6 : 1,
            }}
          >
            {/* 节点头部 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                <Space size={8}>
                  <Text strong style={{ fontSize: 15, color: node.status === 'locked' ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                    {node.title}
                  </Text>
                  <Tag color={cfg.color === '#d9d9d9' ? 'default' : cfg.color}>{cfg.label}</Tag>
                </Space>
                <Paragraph type="secondary" style={{ margin: '6px 0 0', fontSize: 13 }}>
                  {node.description}
                </Paragraph>
              </div>

              <Space size={12} style={{ flexShrink: 0, marginLeft: 16 }}>
                {node.duration && (
                  <Tooltip title="预计时长">
                    <Text type="secondary" style={{ fontSize: 12 }}>⏱ {node.duration}</Text>
                  </Tooltip>
                )}
                {node.score != null && (
                  <Tooltip title="得分">
                    <Tag color={node.score >= 85 ? 'success' : node.score >= 60 ? 'warning' : 'error'}>
                      {node.score}分
                    </Tag>
                  </Tooltip>
                )}
                {node.status !== 'locked' && (
                  <CaretRightOutlined
                    style={{
                      fontSize: 12, color: 'var(--text-muted)',
                      transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                      transition: 'transform 0.2s',
                    }}
                  />
                )}
              </Space>
            </div>

            {/* 技能标签 */}
            {node.skillTags && (
              <div style={{ marginTop: 10 }}>
                <Space size={4} wrap>
                  {node.skillTags.map(sk => {
                    const tag = SKILL_TAGS[sk]
                    return tag ? (
                      <Tag key={sk} color={tag.color} style={{ fontSize: 11, lineHeight: '18px' }}>
                        {tag.label}
                      </Tag>
                    ) : null
                  })}
                </Space>
              </div>
            )}

            {/* 展开资源列表 */}
            {isExpanded && node.resources && (
              <div className="timeline-resources" style={{ marginTop: 14 }}>
                <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
                  学习资源
                </Text>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {node.resources.map((res, ri) => {
                    const rt = RESOURCE_TYPES[res.type] || {}
                    return (
                      <div
                        key={ri}
                        className="resource-item"
                        style={{
                          display: 'flex', alignItems: 'center', gap: 8,
                          padding: '6px 10px', borderRadius: 6,
                          background: 'var(--surface-secondary)', border: '1px solid var(--border)',
                          fontSize: 13,
                        }}
                      >
                        <span>{rt.icon || '📌'}</span>
                        <span style={{ flex: 1 }}>{res.title}</span>
                        <Text type="secondary" style={{ fontSize: 11 }}>{res.duration}</Text>
                        {node.status !== 'locked' && (
                          <Tag style={{ fontSize: 10, lineHeight: '16px' }}>{rt.label}</Tag>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }
}
