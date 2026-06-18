import { useState, useId } from 'react'
import { Card, Typography, Tag, Switch, Space, Tooltip } from 'antd'
import { QuestionCircleOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { useTheme } from '../contexts/ThemeContext'

const { Text, Title } = Typography

// ─── 布局常量 ──────────────────────────────────────
const PAD_LEFT = 52
const PAD_RIGHT = 20
const PAD_TOP = 16
const PAD_BOTTOM = 36
const WIDTH = 640
const HEIGHT = 260

const CHART_W = WIDTH - PAD_LEFT - PAD_RIGHT
const CHART_H = HEIGHT - PAD_TOP - PAD_BOTTOM

// ─── 艾宾浩斯遗忘曲线数据（无复习） ──────────────
const FORGETTING_POINTS = [
  { time: 0,     label: '学完即刻', rate: 100 },
  { time: 0.014, label: '20 分钟',  rate: 58 },
  { time: 0.042, label: '1 小时',   rate: 44 },
  { time: 0.375, label: '9 小时',    rate: 36 },
  { time: 1,     label: '1 天',     rate: 33 },
  { time: 2,     label: '2 天',     rate: 28 },
  { time: 6,     label: '6 天',     rate: 25 },
  { time: 31,    label: '31 天',    rate: 21 },
]

// ─── 间隔复习曲线数据 ─────────────────────────────
const SPACED_POINTS = [
  { time: 0,     rate: 100, review: false },
  { time: 0.014, rate: 58,  review: false },
  { time: 0.042, rate: 44,  review: false },
  { time: 0.375, rate: 36,  review: false },
  { time: 1,     rate: 33,  review: true,  reviewLabel: '第 1 次复习', afterRate: 90 },
  { time: 1.5,   rate: 72,  review: false },
  { time: 3,     rate: 50,  review: true,  reviewLabel: '第 2 次复习', afterRate: 95 },
  { time: 4,     rate: 78,  review: false },
  { time: 7,     rate: 62,  review: true,  reviewLabel: '第 3 次复习', afterRate: 97 },
  { time: 10,    rate: 82,  review: false },
  { time: 30,    rate: 85,  review: false },
]

// 对数尺度映射：将实际天数映射到 [0, 1] 区间
function logScale(day) {
  if (day <= 0) return 0
  return Math.log10(day + 1) / Math.log10(32) // max 31 days → log10(32)
}

function xPos(day) {
  return PAD_LEFT + logScale(day) * CHART_W
}

function yPos(rate) {
  return PAD_TOP + CHART_H - (rate / 100) * CHART_H
}

// ─── 工具函数 ──────────────────────────────────────
function buildCurvePath(points, getX, getY) {
  if (!points.length) return ''
  let d = `M ${getX(points[0]).toFixed(1)} ${getY(points[0]).toFixed(1)}`
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1]
    const curr = points[i]
    const x0 = getX(prev)
    const y0 = getY(prev)
    const x1 = getX(curr)
    const y1 = getY(curr)
    const cpx = x0 + (x1 - x0) * 0.4
    d += ` C ${cpx.toFixed(1)} ${y0.toFixed(1)}, ${cpx.toFixed(1)} ${y1.toFixed(1)}, ${x1.toFixed(1)} ${y1.toFixed(1)}`
  }
  return d
}

/**
 * 艾宾浩斯遗忘曲线组件
 *
 * 展示两种记忆保留曲线：
 * 1. 自然遗忘曲线（虚线）— 不复习的情况下记忆快速衰减
 * 2. 间隔复习曲线（实线）— 科学复习将记忆维持在高水平
 *
 * @param {object}  props.style      - 外层容器样式
 * @param {boolean} props.showReview  - 是否默认显示复习曲线（默认 true）
 * @param {boolean} props.compact     - 紧凑模式（隐藏说明文字）
 */
export default function ForgettingCurve({ style, showReview = true, compact = false }) {
  const [showSpaced, setShowSpaced] = useState(showReview)
  const [tooltip, setTooltip] = useState(null)
  const gradientId = useId().replace(/:/g, '')
  const clipId = useId().replace(/:/g, '')
  const { resolved } = useTheme()
  const isDark = resolved === 'dark'

  // ── 主题色彩 ────────────────────────────
  const colors = {
    forgettingLine: '#f59e0b',       // 遗忘曲线 — 琥珀
    forgettingFill: isDark ? 'rgba(245,158,11,0.08)' : 'rgba(245,158,11,0.1)',
    spacedLine: '#22c55e',           // 复习曲线 — 绿色
    spacedFill: isDark ? 'rgba(34,197,94,0.08)' : 'rgba(34,197,94,0.1)',
    reviewDot: '#1677ff',            // 复习点 — 蓝色
    reviewGlow: 'rgba(22,119,255,0.3)',
    gridLine: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
    axisText: isDark ? 'rgba(255,255,255,0.45)' : '#999',
    axisLine: isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)',
    titleText: isDark ? 'rgba(255,255,255,0.85)' : '#1a1a2e',
    subtitleText: isDark ? 'rgba(255,255,255,0.45)' : '#8c8c8c',
  }

  // Y 轴刻度
  const yTicks = [0, 20, 40, 60, 80, 100]

  // X 轴刻度（对数尺度上的关键时间点）
  const xTicks = [
    { day: 0,     label: '0' },
    { day: 0.014, label: '20分' },
    { day: 1,     label: '1天' },
    { day: 7,     label: '7天' },
    { day: 31,    label: '31天' },
  ]

  // ── 构建路径 ────────────────────────────
  const forgettingPath = buildCurvePath(
    FORGETTING_POINTS,
    (p) => xPos(p.time),
    (p) => yPos(p.rate),
  )

  const spacedPath = buildCurvePath(
    SPACED_POINTS,
    (p) => xPos(p.time),
    (p) => yPos(p.rate),
  )

  // 复习点（包含回升后的点）
  const reviewMarkers = SPACED_POINTS.filter(p => p.review)

  // ── 遗忘曲线面积闭合 ───────────────────
  const firstFP = FORGETTING_POINTS[0]
  const lastFP = FORGETTING_POINTS[FORGETTING_POINTS.length - 1]
  const forgettingArea = [
    forgettingPath,
    `L ${xPos(lastFP.time).toFixed(1)} ${yPos(0).toFixed(1)}`,
    `L ${xPos(firstFP.time).toFixed(1)} ${yPos(0).toFixed(1)}`,
    'Z',
  ].join(' ')

  const firstSP = SPACED_POINTS[0]
  const lastSP = SPACED_POINTS[SPACED_POINTS.length - 1]
  const spacedArea = [
    spacedPath,
    `L ${xPos(lastSP.time).toFixed(1)} ${yPos(0).toFixed(1)}`,
    `L ${xPos(firstSP.time).toFixed(1)} ${yPos(0).toFixed(1)}`,
    'Z',
  ].join(' ')

  return (
    <Card
      className="forgetting-curve-card"
      style={{
        borderRadius: 14,
        border: '1px solid var(--border)',
        background: 'var(--bg-card)',
        ...style,
      }}
      styles={{ body: { padding: compact ? '16px 20px' : '20px 24px' } }}
    >
      {/* 标题栏 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: compact ? 8 : 12 }}>
        <Space size={8}>
          <div style={{
            width: 32, height: 32, borderRadius: 10,
            background: isDark ? 'rgba(139,92,246,0.15)' : 'linear-gradient(135deg, #f5f3ff, #ede9fe)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, color: '#8b5cf6',
          }}>
            🧠
          </div>
          <div>
            <Title level={5} style={{ margin: 0, fontSize: 15, color: 'var(--text-primary)' }}>
              艾宾浩斯遗忘曲线
            </Title>
            {!compact && (
              <Text style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                科学复习，对抗遗忘
              </Text>
            )}
          </div>
        </Space>

        <Tooltip title="显示间隔复习效果">
          <Space size={6}>
            <Text style={{ fontSize: 12, color: 'var(--text-muted)' }}>间隔复习</Text>
            <Switch
              size="small"
              checked={showSpaced}
              onChange={setShowSpaced}
            />
          </Space>
        </Tooltip>
      </div>

      {/* 图表 */}
      <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          width="100%"
          height={HEIGHT}
          style={{ display: 'block', minWidth: 380 }}
        >
          <defs>
            {/* 遗忘曲线渐变 */}
            <linearGradient id={`${gradientId}-forget`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={colors.forgettingLine} stopOpacity={0.2} />
              <stop offset="100%" stopColor={colors.forgettingLine} stopOpacity={0.01} />
            </linearGradient>
            {/* 复习曲线渐变 */}
            <linearGradient id={`${gradientId}-space`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={colors.spacedLine} stopOpacity={0.2} />
              <stop offset="100%" stopColor={colors.spacedLine} stopOpacity={0.01} />
            </linearGradient>
            {/* 复习点发光 */}
            <filter id={`${gradientId}-glow`}>
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <clipPath id={clipId}>
              <rect x={PAD_LEFT - 4} y={PAD_TOP - 4} width={CHART_W + 8} height={CHART_H + 8} />
            </clipPath>
          </defs>

          {/* Y 轴网格线 + 标签 */}
          {yTicks.map((tick) => {
            const y = yPos(tick)
            return (
              <g key={`y-${tick}`}>
                <line
                  x1={PAD_LEFT} x2={WIDTH - PAD_RIGHT} y1={y} y2={y}
                  stroke={colors.gridLine} strokeWidth={1}
                />
                <text
                  x={PAD_LEFT - 8} y={y + 4}
                  textAnchor="end" fill={colors.axisText}
                  fontSize={11} fontFamily="ui-monospace, monospace"
                >
                  {tick}
                </text>
              </g>
            )
          })}

          {/* Y 轴标题 */}
          <text
            x={10} y={HEIGHT / 2}
            textAnchor="middle" fill={colors.axisText}
            fontSize={11} transform={`rotate(-90, 10, ${HEIGHT / 2})`}
          >
            记忆保留 (%)
          </text>

          {/* X 轴标签 */}
          {xTicks.map((t) => {
            const x = xPos(t.day)
            return (
              <g key={`x-${t.day}`}>
                <line
                  x1={x} x2={x} y1={PAD_TOP + CHART_H} y2={PAD_TOP + CHART_H + 5}
                  stroke={colors.axisLine} strokeWidth={1}
                />
                <text
                  x={x} y={HEIGHT - 8}
                  textAnchor="middle" fill={colors.axisText}
                  fontSize={11}
                >
                  {t.label}
                </text>
              </g>
            )
          })}

          {/* X 轴 */}
          <line
            x1={PAD_LEFT} x2={WIDTH - PAD_RIGHT}
            y1={yPos(0)} y2={yPos(0)}
            stroke={colors.axisLine} strokeWidth={1}
          />

          {/* 遗忘曲线面积 */}
          <path
            d={forgettingArea}
            fill={`url(#${gradientId}-forget)`}
            clipPath={`url(#${clipId})`}
          />

          {/* 复习曲线面积 */}
          {showSpaced && (
            <path
              d={spacedArea}
              fill={`url(#${gradientId}-space)`}
              clipPath={`url(#${clipId})`}
            />
          )}

          {/* 100% 参考线 */}
          <line
            x1={PAD_LEFT} x2={WIDTH - PAD_RIGHT}
            y1={yPos(100)} y2={yPos(100)}
            stroke={colors.gridLine} strokeWidth={1} strokeDasharray="4,4"
          />

          {/* 遗忘曲线 — 虚线 */}
          <path
            d={forgettingPath}
            fill="none"
            stroke={colors.forgettingLine}
            strokeWidth={2.5}
            strokeDasharray="8,4"
            strokeLinecap="round"
            strokeLinejoin="round"
            clipPath={`url(#${clipId})`}
          />

          {/* 复习曲线 — 实线 */}
          {showSpaced && (
            <path
              d={spacedPath}
              fill="none"
              stroke={colors.spacedLine}
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeLinejoin="round"
              clipPath={`url(#${clipId})`}
            />
          )}

          {/* 遗忘曲线数据点 */}
          {FORGETTING_POINTS.map((p, i) => {
            const x = xPos(p.time)
            const y = yPos(p.rate)
            return (
              <g key={`fp-${i}`}
                onMouseEnter={(e) => setTooltip({
                  cx: x, cy: y,
                  x: e.clientX, y: e.clientY,
                  label: p.label,
                  rate: p.rate,
                  type: 'forget',
                })}
                onMouseLeave={() => setTooltip(null)}
                style={{ cursor: 'pointer' }}
              >
                <circle cx={x} cy={y} r={12} fill="transparent" />
                <circle cx={x} cy={y} r={4} fill={i === 0 ? colors.spacedLine : colors.forgettingLine} stroke="#fff" strokeWidth={1.5} />
              </g>
            )
          })}

          {/* 复习曲线数据点 */}
          {showSpaced && SPACED_POINTS.map((p, i) => {
            const x = xPos(p.time)
            const y = yPos(p.rate)
            return (
              <g key={`sp-${i}`}
                onMouseEnter={(e) => setTooltip({
                  cx: x, cy: y,
                  x: e.clientX, y: e.clientY,
                  label: `${p.time} 天`,
                  rate: p.rate,
                  type: p.review ? 'review' : 'spaced',
                })}
                onMouseLeave={() => setTooltip(null)}
                style={{ cursor: 'pointer' }}
              >
                <circle cx={x} cy={y} r={12} fill="transparent" />
                <circle
                  cx={x} cy={y}
                  r={p.review ? 5 : 3}
                  fill={p.review ? colors.reviewDot : colors.spacedLine}
                  stroke={p.review ? '#fff' : 'none'}
                  strokeWidth={2}
                  filter={p.review ? `url(#${gradientId}-glow)` : undefined}
                />
              </g>
            )
          })}

          {/* 复习回升箭头 + after 点 */}
          {showSpaced && reviewMarkers.map((m, i) => (
            <g key={`rv-${i}`}>
              {/* 回升指示线 */}
              <line
                x1={xPos(m.time)} y1={yPos(m.rate)}
                x2={xPos(m.time)} y2={yPos(m.afterRate)}
                stroke={colors.reviewDot}
                strokeWidth={1.5}
                strokeDasharray="3,3"
              />
              {/* 回升后圆点 */}
              <circle
                cx={xPos(m.time)} cy={yPos(m.afterRate)}
                r={5}
                fill={colors.spacedLine}
                stroke="#fff"
                strokeWidth={2}
                filter={`url(#${gradientId}-glow)`}
              />
              {/* 复习标签 */}
              <text
                x={xPos(m.time)} y={yPos(m.afterRate) - 10}
                textAnchor="middle" fill={colors.reviewDot}
                fontSize={10} fontWeight={600}
              >
                {m.reviewLabel}
              </text>
              {/* 回升百分比 */}
              <text
                x={xPos(m.time)} y={yPos(m.afterRate) + 4}
                textAnchor="middle" fill={colors.reviewDot}
                fontSize={10} fontWeight={700}
              >
                ↑{m.afterRate}%
              </text>
            </g>
          ))}

          {/* 图例 */}
          <g transform={`translate(${WIDTH - PAD_RIGHT - 260}, ${PAD_TOP - 4})`}>
            {/* 自然遗忘 */}
            <line x1={0} y1={0} x2={22} y2={0}
              stroke={colors.forgettingLine} strokeWidth={2} strokeDasharray="6,3" />
            <text x={28} y={4} fill={colors.axisText} fontSize={11}>自然遗忘</text>
            {/* 间隔复习 */}
            {showSpaced && (
              <>
                <line x1={82} y1={0} x2={104} y2={0}
                  stroke={colors.spacedLine} strokeWidth={2} />
                <text x={110} y={4} fill={colors.axisText} fontSize={11}>间隔复习</text>

                <circle cx={182} cy={0} r={4} fill={colors.reviewDot} stroke="#fff" strokeWidth={1.5} />
                <text x={192} y={4} fill={colors.axisText} fontSize={11}>复习点</text>
              </>
            )}
          </g>
        </svg>

        {/* 悬浮提示 */}
        {tooltip && (
          <div
            style={{
              position: 'fixed',
              left: tooltip.x + 14,
              top: tooltip.y - 36,
              background: isDark ? 'rgba(30,30,40,0.95)' : 'rgba(0,0,0,0.85)',
              color: '#fff',
              padding: '6px 12px',
              borderRadius: 6,
              fontSize: 12,
              pointerEvents: 'none',
              zIndex: 1000,
              whiteSpace: 'nowrap',
              boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
            }}
          >
            <Text style={{ color: '#fff', fontSize: 12 }}>
              📍 {tooltip.label}  ·  保留 <b>{tooltip.rate}%</b>
              {tooltip.type === 'review' && (
                <Tag color="blue" style={{ marginLeft: 6, fontSize: 10, lineHeight: '16px' }}>复习</Tag>
              )}
            </Text>
          </div>
        )}
      </div>

      {/* 底部提示 */}
      {!compact && showSpaced && (
        <div style={{
          marginTop: 10, padding: '8px 12px', borderRadius: 8,
          background: 'var(--surface-secondary)',
          display: 'flex', alignItems: 'flex-start', gap: 8,
        }}>
          <ThunderboltOutlined style={{ color: '#8b5cf6', marginTop: 2, fontSize: 13 }} />
          <Text style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            <strong>间隔复习</strong>：学习后 1 天、3 天、7 天、30 天分别复习，可将长期记忆保留率从 <Text style={{ color: '#f59e0b', fontWeight: 600 }}>21%</Text> 提升至 <Text style={{ color: '#22c55e', fontWeight: 600 }}>85%+</Text>
          </Text>
        </div>
      )}
    </Card>
  )
}
