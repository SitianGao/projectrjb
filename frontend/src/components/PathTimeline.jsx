import { useState } from 'react'
import { Card, Tag, Typography, Progress, Collapse, Tooltip, Space } from 'antd'
import {
  CheckCircleFilled,
  PlayCircleFilled,
  ClockCircleFilled,
  LockFilled,
  CaretRightOutlined,
  BookOutlined,
  StarFilled,
} from '@ant-design/icons'
import { SKILL_TAGS, RESOURCE_TYPES } from '../mock/learningPathData'

const { Text, Title, Paragraph } = Typography

// 状态配置
const statusConfig = {
  completed: { icon: CheckCircleFilled, color: '#52c41a', bg: '#f6ffed', label: '已完成', dot: '#52c41a' },
  in_progress: { icon: PlayCircleFilled, color: '#1677ff', bg: '#e6f4ff', label: '进行中', dot: '#1677ff', pulse: true },
  pending: { icon: ClockCircleFilled, color: '#d9d9d9', bg: '#fafafa', label: '待开始', dot: '#bfbfbf' },
  locked: { icon: LockFilled, color: '#d9d9d9', bg: '#f5f5f5', label: '未解锁', dot: '#d9d9d9' },
}

/**
 * 学习路径时间线
 * @param {Array}  props.nodes       - 路径节点数组
 * @param {number} props.overallProgress - 整体进度 0-100
 * @param {string} props.title       - 路径标题
 * @param {boolean} props.loading
 * @param {Function} props.onNodeClick
 */
export default function PathTimeline({ nodes = [], overallProgress = 0, title = '', loading = false, onNodeClick }) {
  const [expandedNode, setExpandedNode] = useState(null)

  if (loading) {
    return (
      <Card loading style={{ minHeight: 200 }} />
    )
  }

  if (!nodes.length) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 48 }}>
          <BookOutlined style={{ fontSize: 40, color: '#d9d9d9' }} />
          <Paragraph type="secondary" style={{ marginTop: 16 }}>暂无学习路径，点击上方按钮生成</Paragraph>
        </div>
      </Card>
    )
  }

  const completedCount = nodes.filter(n => n.status === 'completed').length
  const progress = overallProgress || Math.round((completedCount / nodes.length) * 100)

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
                  {completedCount}/{nodes.length} 节点已完成 · 进度 {progress}%
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

      {/* 时间线节点 */}
      <div className="timeline-track">
        {nodes.map((node, idx) => {
          const cfg = statusConfig[node.status] || statusConfig.pending
          const Icon = cfg.icon
          const isActive = node.status === 'in_progress'
          const isExpanded = expandedNode === node.id
          const isLast = idx === nodes.length - 1

          return (
            <div key={node.id} className="timeline-node-wrapper">
              {/* 连接线 + 节点 */}
              <div className="timeline-row">
                {/* 左侧：指示器 */}
                <div className="timeline-indicator">
                  <div className={`timeline-dot ${isActive ? 'pulse' : ''}`}
                    style={{ background: cfg.dot, boxShadow: isActive ? `0 0 0 4px ${cfg.color}30` : 'none' }}
                  >
                    <Icon style={{ fontSize: 14, color: node.status === 'pending' || node.status === 'locked' ? '#999' : '#fff' }} />
                  </div>
                  {!isLast && <div className="timeline-line" style={{ background: node.status === 'completed' ? '#52c41a' : '#e8e8e8' }} />}
                </div>

                {/* 右侧：内容卡片 */}
                <div
                  className={`timeline-card ${isActive ? 'active' : ''} ${node.status === 'locked' ? 'locked' : ''}`}
                  onClick={() => {
                    if (node.status !== 'locked') {
                      setExpandedNode(isExpanded ? null : node.id)
                      onNodeClick?.(node)
                    }
                  }}
                  style={{
                    background: cfg.bg,
                    borderColor: isActive ? cfg.color : 'transparent',
                    cursor: node.status === 'locked' ? 'default' : 'pointer',
                    opacity: node.status === 'locked' ? 0.6 : 1,
                  }}
                >
                  {/* 节点头部 */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <Space size={8}>
                        <Text strong style={{ fontSize: 15, color: node.status === 'locked' ? '#999' : '#1a1a2e' }}>
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
                            fontSize: 12, color: '#999',
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
                                background: '#fff', border: '1px solid #f0f0f0',
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
        })}
      </div>
    </div>
  )
}
