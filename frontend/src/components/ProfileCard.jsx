import { useEffect, useRef, useState, useMemo } from 'react'
import { Card, Tag, Progress, Space, Typography, Tooltip, Descriptions, Row, Col } from 'antd'
import {
  BookOutlined,
  StarOutlined,
  TrophyOutlined,
  FieldTimeOutlined,
  BulbOutlined,
  IdcardOutlined,
  RadarChartOutlined,
} from '@ant-design/icons'
import { formatPercent } from '../utils/format'

const { Text, Title } = Typography

// ========== 六维定义 ==========
const DIMENSIONS = [
  { key: 'knowledge',   label: '知识掌握',   icon: '📚', color: '#aa3bff', description: '核心知识点的掌握程度' },
  { key: 'ability',     label: '学习能力',   icon: '🧠', color: '#6366f1', description: '理解与运用新知识的能力' },
  { key: 'thinking',    label: '思维水平',   icon: '💡', color: '#52c41a', description: '批判性思维与问题解决能力' },
  { key: 'style',       label: '风格适配',   icon: '🎯', color: '#fa8c16', description: '学习风格与推荐策略的匹配度' },
  { key: 'progress',    label: '学习进度',   icon: '📈', color: '#1677ff', description: '当前阶段目标的完成进度' },
  { key: 'goalClarity', label: '目标明确',   icon: '🏆', color: '#eb2f96', description: '学习目标的清晰与规划程度' },
]

// ========== Mock 画像数据 ==========
const MOCK_PROFILE = {
  name: '张小明',
  strengths: ['数学', '物理', '化学'],
  weaknesses: ['英语', '语文'],
  style: '实践型',
  level: '中级',
  progress: 68,
  dimensions: {
    knowledge: 82,
    ability: 70,
    thinking: 75,
    style: 72,
    progress: 68,
    goalClarity: 85,
  },
  topics: [
    { name: '二次函数', accuracy: 0.92 },
    { name: '力学基础', accuracy: 0.85 },
    { name: '电路分析', accuracy: 0.78 },
    { name: '英语语法', accuracy: 0.55 },
    { name: '三角函数', accuracy: 0.88 },
  ],
}

// ========== 雷达图常量 ==========
const RADAR_CENTER = 160
const RADAR_RADIUS = 100
const RADAR_LEVELS = 4        // 同心辅助环数
const RADAR_ANGLES = DIMENSIONS.map((_, i) => (Math.PI * 2 * i) / DIMENSIONS.length - Math.PI / 2)

// ========== 样式常量 ==========
const CARD_STYLE = {
  borderRadius: 12,
  border: '1px solid var(--border, #e5e4e7)',
  background: 'rgba(255,255,255,0.7)',
  backdropFilter: 'blur(6px)',
}

const SECTION_STYLE = (accentColor = 'rgba(170,59,255,0.03)', borderColor = 'rgba(170,59,255,0.08)') => ({
  background: accentColor,
  borderRadius: 10,
  padding: '10px 14px',
  border: `1px solid ${borderColor}`,
})

const ICON_WRAP_STYLE = (size = 28, radius = 7) => ({
  width: size,
  height: size,
  borderRadius: radius,
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: Math.round(size * 0.5),
  color: '#fff',
  background: 'linear-gradient(135deg, #aa3bff 0%, #6366f1 100%)',
  boxShadow: '0 3px 10px rgba(170,59,255,0.25)',
})

/**
 * 计算六维得分（0-100），优先使用 profile.dimensions，否则根据已有字段推断
 */
function deriveDimensions(profile) {
  if (!profile) return DIMENSIONS.reduce((acc, d) => ({ ...acc, [d.key]: 0 }), {})

  if (profile.dimensions) return profile.dimensions

  // 从已有字段推断
  const topicAvg = profile.topics?.length
    ? profile.topics.reduce((s, t) => s + (t.accuracy > 1 ? t.accuracy : t.accuracy * 100), 0) / profile.topics.length
    : 0

  const levelMap = { '初级': 30, '中级': 60, '高级': 90 }
  const levelScore = levelMap[profile.level] || 0

  const strengthsCount = profile.strengths?.length || 0
  const weaknessesCount = profile.weaknesses?.length || 0

  return {
    knowledge:   Math.round(Math.max(topicAvg, levelScore * 0.8)),
    ability:     Math.round(Math.max(levelScore, strengthsCount * 15 + 20)),
    thinking:    Math.round(Math.min(95, strengthsCount * 18 + weaknessesCount * 8 + 15)),
    style:       profile.style ? 70 : 15,
    progress:    profile.progress || 0,
    goalClarity: (profile.name ? 40 : 0) + (profile.style ? 30 : 0) + (profile.level ? 30 : 0),
  }
}

/**
 * 计算雷达图顶点坐标
 */
function getRadarPoint(angle, value, centerX = RADAR_CENTER, centerY = RADAR_CENTER, radius = RADAR_RADIUS) {
  const r = (value / 100) * radius
  return {
    x: centerX + r * Math.cos(angle),
    y: centerY + r * Math.sin(angle),
  }
}

/**
 * 生成雷达多边形 points 字符串
 */
function buildPolygon(dimensions, angles = RADAR_ANGLES) {
  return angles
    .map((angle, i) => {
      const dim = DIMENSIONS[i]
      const val = dimensions[dim.key] || 0
      const { x, y } = getRadarPoint(angle, val)
      return `${x},${y}`
    })
    .join(' ')
}

// ========== 六维雷达图 SVG 组件 ==========
function RadarChart({ dimensions, animated = true }) {
  const [animProgress, setAnimProgress] = useState(animated ? 0 : 1)
  const rafRef = useRef(null)

  useEffect(() => {
    if (!animated) {
      setAnimProgress(1)
      return
    }
    const start = performance.now()
    const duration = 800 // ms
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration)
      // easeOutCubic
      setAnimProgress(1 - Math.pow(1 - p, 3))
      if (p < 1) rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [animated])

  // 动画中的维度值
  const animatedDims = useMemo(() => {
    const result = {}
    for (const d of DIMENSIONS) {
      result[d.key] = (dimensions[d.key] || 0) * animProgress
    }
    return result
  }, [dimensions, animProgress])

  const dataPolygon = buildPolygon(animatedDims)

  return (
    <svg
      viewBox={`0 0 ${RADAR_CENTER * 2} ${RADAR_CENTER * 2}`}
      style={{ width: '100%', maxWidth: 320, display: 'block', margin: '0 auto' }}
    >
      {/* 渐变定义 */}
      <defs>
        <radialGradient id="radarGradient" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(170,59,255,0.35)" />
          <stop offset="70%" stopColor="rgba(99,102,241,0.12)" />
          <stop offset="100%" stopColor="rgba(99,102,241,0)" />
        </radialGradient>
        <filter id="radarGlow">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* 同心网格 */}
      {Array.from({ length: RADAR_LEVELS }, (_, lvl) => {
        const r = (RADAR_RADIUS / RADAR_LEVELS) * (lvl + 1)
        const points = RADAR_ANGLES.map((a) => {
          const x = RADAR_CENTER + r * Math.cos(a)
          const y = RADAR_CENTER + r * Math.sin(a)
          return `${x},${y}`
        }).join(' ')
        return (
          <polygon
            key={lvl}
            points={points}
            fill="none"
            stroke="rgba(0,0,0,0.06)"
            strokeWidth="1"
          />
        )
      })}

      {/* 轴线 */}
      {RADAR_ANGLES.map((a, i) => {
        const ex = RADAR_CENTER + RADAR_RADIUS * Math.cos(a)
        const ey = RADAR_CENTER + RADAR_RADIUS * Math.sin(a)
        return (
          <line
            key={i}
            x1={RADAR_CENTER}
            y1={RADAR_CENTER}
            x2={ex}
            y2={ey}
            stroke="rgba(0,0,0,0.06)"
            strokeWidth="1"
          />
        )
      })}

      {/* 数据填充多边形 */}
      <polygon
        points={dataPolygon}
        fill="url(#radarGradient)"
        stroke="rgba(170,59,255,0.5)"
        strokeWidth="2"
        strokeLinejoin="round"
        filter="url(#radarGlow)"
        style={{ transition: 'all 0.15s ease-out' }}
      />

      {/* 数据顶点 */}
      {RADAR_ANGLES.map((a, i) => {
        const dim = DIMENSIONS[i]
        const val = animatedDims[dim.key] || 0
        const { x, y } = getRadarPoint(a, val)
        return (
          <circle
            key={i}
            cx={x}
            cy={y}
            r="4"
            fill="#fff"
            stroke={dim.color}
            strokeWidth="2.5"
            filter="url(#radarGlow)"
          />
        )
      })}

      {/* 标签 */}
      {RADAR_ANGLES.map((a, i) => {
        const dim = DIMENSIONS[i]
        // 标签放在顶点外侧
        const labelR = RADAR_RADIUS + 28
        const lx = RADAR_CENTER + labelR * Math.cos(a)
        const ly = RADAR_CENTER + labelR * Math.sin(a)
        const textAnchor =
          lx < RADAR_CENTER - 20 ? 'end' : lx > RADAR_CENTER + 20 ? 'start' : 'middle'
        return (
          <text
            key={i}
            x={lx}
            y={ly}
            textAnchor={textAnchor}
            dominantBaseline="central"
            fontSize="12"
            fontWeight={600}
            fill="#1a1a2e"
            style={{ fontFamily: 'var(--sans, system-ui)' }}
          >
            {dim.label}
          </text>
        )
      })}

      {/* 中心数值 */}
      <text
        x={RADAR_CENTER}
        y={RADAR_CENTER}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize="14"
        fontWeight={700}
        fill="var(--accent, #aa3bff)"
        style={{ fontFamily: 'var(--mono, ui-monospace)' }}
      >
        {Math.round(
          Object.values(animatedDims).reduce((a, b) => a + b, 0) / DIMENSIONS.length
        )}
        <tspan fontSize="10" fontWeight={400}>分</tspan>
      </text>
    </svg>
  )
}

// ========== 六维条形列表（辅助视图） ==========
function DimensionBars({ dimensions }) {
  return (
    <Space direction="vertical" size={6} style={{ width: '100%' }}>
      {DIMENSIONS.map((dim) => {
        const val = dimensions[dim.key] || 0
        return (
          <div key={dim.key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tooltip title={dim.description}>
              <Text style={{ fontSize: 12, minWidth: 56, color: '#1a1a2e' }}>
                {dim.label}
              </Text>
            </Tooltip>
            <Progress
              percent={val}
              size="small"
              showInfo={false}
              strokeColor={{
                '0%': dim.color,
                '100%': dim.color + '99',
              }}
              trailColor="rgba(0,0,0,0.05)"
              style={{ flex: 1 }}
            />
            <Text
              style={{
                fontSize: 12,
                fontWeight: 600,
                fontFamily: 'var(--mono, ui-monospace)',
                color: dim.color,
                minWidth: 32,
                textAlign: 'right',
              }}
            >
              {val}
            </Text>
          </div>
        )
      })}
    </Space>
  )
}

/**
 * 学生画像卡片 — 六维雷达图 + 详细信息
 *
 * @param {Object} props
 * @param {Object} props.profile   - 画像数据
 * @param {Object} props.profile.dimensions - 六维得分 {knowledge, ability, thinking, style, progress, goalClarity}
 * @param {string} props.profile.name       - 学生姓名
 * @param {Array}  props.profile.strengths  - 优势学科
 * @param {Array}  props.profile.weaknesses - 薄弱学科
 * @param {string} props.profile.style      - 学习风格
 * @param {string} props.profile.level      - 当前水平
 * @param {number} props.profile.progress   - 整体进度 0-100
 * @param {Array}  props.profile.topics     - 知识点掌握情况
 * @param {boolean} props.loading           - 加载中
 */
export default function ProfileCard({ profile, loading = false }) {
  // 使用 ?? 处理 null 和 undefined，确保开发时能看到 mock 数据
  const effectiveProfile = profile ?? MOCK_PROFILE
  const dimensions = useMemo(() => deriveDimensions(effectiveProfile), [effectiveProfile])

  // 雷达图是否开启动画（首次有数据时动画）
  const [hasEverHadData, setHasEverHadData] = useState(false)
  useEffect(() => {
    if (effectiveProfile && !hasEverHadData) setHasEverHadData(true)
  }, [effectiveProfile, hasEverHadData])

  const levelColorMap = {
    '初级': 'blue',
    '中级': 'orange',
    '高级': 'red',
  }

  // ========== 空状态（无有效画像数据时展示） ==========
  if (!effectiveProfile && !loading) {
    return (
      <Card
        loading={loading}
        style={{
          ...CARD_STYLE,
          textAlign: 'center',
          minHeight: 280,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ padding: '32px 0' }}>
          <div style={ICON_WRAP_STYLE(64, 16)}>
            <IdcardOutlined style={{ fontSize: 28 }} />
          </div>
          <div style={{ marginTop: 16 }}>
            <Text style={{ color: 'var(--text-h, #08060d)', fontSize: 15, fontWeight: 500 }}>
              暂无画像数据
            </Text>
            <br />
            <Text style={{ color: 'var(--text, #6b6375)', fontSize: 13 }}>
              在对话区与助手聊聊，完善你的六维学习画像
            </Text>
          </div>
          {/* 空状态雷达图 */}
          <div style={{ marginTop: 16, opacity: 0.25 }}>
            <RadarChart
              dimensions={DIMENSIONS.reduce((acc, d) => ({ ...acc, [d.key]: 15 }), {})}
              animated={false}
            />
          </div>
        </div>
      </Card>
    )
  }

  // ========== 有数据 ==========
  return (
    <Card
      loading={loading}
      title={
        <Space>
          <div style={ICON_WRAP_STYLE(28, 7)}>
            <RadarChartOutlined />
          </div>
          <Title level={5} style={{ margin: 0, color: '#2c2c2c' }}>
            六维学习画像
          </Title>
        </Space>
      }
      style={CARD_STYLE}
      styles={{ body: { padding: '12px 16px 16px' } }}
      className="tech-profile-card"
    >
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {/* ========== 六维雷达图 + 维度条（并排） ========== */}
        <div
          style={{
            background: 'rgba(170,59,255,0.02)',
            borderRadius: 12,
            padding: '12px 8px 4px',
            border: '1px solid rgba(170,59,255,0.06)',
          }}
        >
          <Row gutter={[8, 8]} align="middle">
            <Col xs={24} sm={12} style={{ display: 'flex', justifyContent: 'center' }}>
              <RadarChart dimensions={dimensions} animated={hasEverHadData} />
            </Col>
            <Col xs={24} sm={12}>
              <DimensionBars dimensions={dimensions} />
            </Col>
          </Row>
        </div>

        {/* ========== 基本信息 ========== */}
        {effectiveProfile?.name && (
          <div style={SECTION_STYLE('rgba(170,59,255,0.03)', 'rgba(170,59,255,0.08)')}>
            <Descriptions column={2} size="small" bordered={false}>
              <Descriptions.Item
                label={<Text style={{ color: '#8c8c8c', fontSize: 12 }}>姓名</Text>}
              >
                <Text strong style={{ color: '#2c2c2c' }}>
                  {effectiveProfile.name}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item
                label={<Text style={{ color: '#8c8c8c', fontSize: 12 }}>学习风格</Text>}
              >
                <Tag
                  icon={<BulbOutlined />}
                  color="purple"
                  style={{
                    borderRadius: 6,
                    background: 'rgba(170,59,255,0.1)',
                    border: '1px solid rgba(170,59,255,0.3)',
                    color: '#7c3aed',
                  }}
                >
                  {effectiveProfile.style || '--'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item
                label={<Text style={{ color: '#8c8c8c', fontSize: 12 }}>当前水平</Text>}
              >
                <Tag
                  color={levelColorMap[effectiveProfile.level] || 'default'}
                  style={{ borderRadius: 6 }}
                >
                  {effectiveProfile.level || '--'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item
                label={<Text style={{ color: '#8c8c8c', fontSize: 12 }}>整体进度</Text>}
              >
                <Progress
                  percent={effectiveProfile.progress || 0}
                  size="small"
                  strokeColor={{ '0%': '#aa3bff', '100%': '#6366f1' }}
                  trailColor="rgba(0,0,0,0.06)"
                  style={{ minWidth: 100, maxWidth: '100%' }}
                />
              </Descriptions.Item>
            </Descriptions>
          </div>
        )}

        {/* ========== 学科评估（优势 / 薄弱 并排） ========== */}
        <div style={SECTION_STYLE('rgba(170,59,255,0.02)', 'rgba(170,59,255,0.06)')}>
          <Row gutter={[16, 8]}>
            <Col xs={24} sm={12}>
              <div style={{ marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                <TrophyOutlined style={{ color: '#52c41a', fontSize: 12 }} />
                <Text strong style={{ color: '#2c2c2c', fontSize: 12 }}>优势学科</Text>
              </div>
              <Space wrap size={4}>
                {effectiveProfile?.strengths?.length > 0 ? (
                  effectiveProfile.strengths.map((s) => (
                    <Tag
                      key={s}
                      style={{
                        borderRadius: 6,
                        background: 'rgba(82,196,26,0.1)',
                        border: '1px solid rgba(82,196,26,0.25)',
                        color: '#389e0d',
                        fontSize: 12,
                      }}
                    >
                      {s}
                    </Tag>
                  ))
                ) : (
                  <Tag color="default" style={{ borderRadius: 6, borderStyle: 'dashed', fontSize: 12 }}>待分析</Tag>
                )}
              </Space>
            </Col>
            <Col xs={24} sm={12}>
              <div style={{ marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                <FieldTimeOutlined style={{ color: '#fa8c16', fontSize: 12 }} />
                <Text strong style={{ color: '#2c2c2c', fontSize: 12 }}>薄弱学科</Text>
              </div>
              <Space wrap size={4}>
                {effectiveProfile?.weaknesses?.length > 0 ? (
                  effectiveProfile.weaknesses.map((w) => (
                    <Tag
                      key={w}
                      style={{
                        borderRadius: 6,
                        background: 'rgba(250,140,22,0.1)',
                        border: '1px solid rgba(250,140,22,0.25)',
                        color: '#d46b08',
                        fontSize: 12,
                      }}
                    >
                      {w}
                    </Tag>
                  ))
                ) : (
                  <Tag color="default" style={{ borderRadius: 6, borderStyle: 'dashed', fontSize: 12 }}>待分析</Tag>
                )}
              </Space>
            </Col>
          </Row>
        </div>

        {/* ========== 知识点掌握 ========== */}
        {effectiveProfile?.topics?.length > 0 && (
          <div style={SECTION_STYLE('rgba(170,59,255,0.03)', 'rgba(170,59,255,0.08)')}>
            <div style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
              <StarOutlined style={{ color: '#aa3bff' }} />
              <Text strong style={{ color: '#2c2c2c', fontSize: 13 }}>
                知识点掌握
              </Text>
            </div>
            {effectiveProfile.topics.map((topic) => {
              const pct = Math.round(
                topic.accuracy > 1 ? topic.accuracy : topic.accuracy * 100,
              )
              return (
                <Tooltip
                  key={topic.name}
                  title={`正确率: ${formatPercent(topic.accuracy)}`}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      marginBottom: 10,
                    }}
                  >
                    <BookOutlined style={{ color: '#aa3bff', fontSize: 13 }} />
                    <Text style={{ minWidth: 72, color: '#2c2c2c', fontSize: 13 }}>
                      {topic.name}
                    </Text>
                    <Progress
                      percent={pct}
                      size="small"
                      showInfo={false}
                      strokeColor={
                        pct >= 80
                          ? { '0%': '#52c41a', '100%': '#73d13d' }
                          : pct >= 60
                            ? { '0%': '#fa8c16', '100%': '#ffc53d' }
                            : { '0%': '#ff4d4f', '100%': '#ff7a45' }
                      }
                      trailColor="rgba(0,0,0,0.06)"
                      style={{ flex: 1 }}
                    />
                    <Text
                      style={{
                        fontSize: 12,
                        fontWeight: 600,
                        fontFamily: 'var(--mono, ui-monospace)',
                        color:
                          pct >= 80
                            ? '#52c41a'
                            : pct >= 60
                              ? '#fa8c16'
                              : '#ff4d4f',
                        minWidth: 32,
                        textAlign: 'right',
                      }}
                    >
                      {pct}%
                    </Text>
                  </div>
                </Tooltip>
              )
            })}
          </div>
        )}
      </Space>
    </Card>
  )
}
