import { useState, useId } from 'react'
import { Typography } from 'antd'

const { Text } = Typography

// 布局常量
const PAD_LEFT = 42
const PAD_RIGHT = 16
const PAD_TOP = 12
const PAD_BOTTOM = 32
const WIDTH = 600
const HEIGHT = 280

/**
 * 评分趋势折线图（纯 SVG，零依赖）
 *
 * @param {Array<{date: string, score: number}>} props.data - 评分数据
 * @param {number} props.height - SVG 高度（默认 280）
 */
export default function ScoreTrendChart({ data = [], height = HEIGHT, loading = false }) {
  const [tooltip, setTooltip] = useState(null)
  const gradientId = useId()
  const clipId = useId()

  if (loading) {
    return (
      <div style={{
        width: '100%', height, display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'linear-gradient(90deg, rgba(0,0,0,0.02) 25%, rgba(0,0,0,0.06) 50%, rgba(0,0,0,0.02) 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite',
        borderRadius: 8,
      }}>
        <span style={{ color: '#ccc', fontSize: 14 }}>加载中...</span>
      </div>
    )
  }

  if (!data.length) {
    return (
      <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>
        暂无评分数据
      </div>
    )
  }

  const chartW = WIDTH - PAD_LEFT - PAD_RIGHT
  const chartH = height - PAD_TOP - PAD_BOTTOM

  // Y 轴刻度（0-100，每 20 分一格）
  const yTicks = [0, 20, 40, 60, 80, 100]
  const yMin = 0
  const yMax = 100

  const xScale = (i) => PAD_LEFT + (i / Math.max(data.length - 1, 1)) * chartW
  const yScale = (score) => PAD_TOP + chartH - ((score - yMin) / (yMax - yMin)) * chartH

  // 构建折线 path
  const linePath = data
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i).toFixed(1)} ${yScale(d.score).toFixed(1)}`)
    .join(' ')

  // 构建面积 path（折线 + 底部闭合）
  const areaPath = [
    linePath,
    `L ${xScale(data.length - 1).toFixed(1)} ${yScale(0).toFixed(1)}`,
    `L ${xScale(0).toFixed(1)} ${yScale(0).toFixed(1)}`,
    'Z',
  ].join(' ')

  // 网格线
  const gridLines = yTicks.map((tick) => {
    const y = yScale(tick)
    return (
      <g key={`grid-${tick}`}>
        <line x1={PAD_LEFT} x2={WIDTH - PAD_RIGHT} y1={y} y2={y}
          stroke="#f0f0f0" strokeWidth={1} />
        <text x={PAD_LEFT - 8} y={y + 4} textAnchor="end"
          fill="#999" fontSize={11} fontFamily="ui-monospace, monospace">
          {tick}
        </text>
      </g>
    )
  })

  // X 轴日期标签
  const dateLabels = data.map((d, i) => {
    const x = xScale(i)
    const label = d.date.length > 5 ? d.date.slice(5) : d.date // "MM-DD"
    return (
      <text key={`date-${i}`} x={x} y={height - 6} textAnchor="middle"
        fill="#999" fontSize={11}>
        {label}
      </text>
    )
  })

  // 数据点
  const dots = data.map((d, i) => {
    const x = xScale(i)
    const y = yScale(d.score)
    const isLast = i === data.length - 1
    return (
      <g key={`dot-${i}`}
        onMouseEnter={(e) => setTooltip({ x: e.clientX, y: e.clientY, date: d.date, score: d.score, index: i })}
        onMouseLeave={() => setTooltip(null)}
        style={{ cursor: 'pointer' }}
      >
        {/* 透明大热区 */}
        <circle cx={x} cy={y} r={14} fill="transparent" />
        {/* 外圈 */}
        <circle cx={x} cy={y} r={5} fill="#fff" stroke={isLast ? '#1677ff' : '#52c41a'} strokeWidth={2.5} />
        {/* 内点 */}
        <circle cx={x} cy={y} r={2.5} fill={isLast ? '#1677ff' : '#52c41a'} />
      </g>
    )
  })

  // 分数标签（最后一个点 + 最高分点）
  const lastIdx = data.length - 1
  const maxIdx = data.reduce((max, d, i) => (d.score > data[max].score ? i : max), 0)
  const labelIndices = new Set([lastIdx, maxIdx])

  const scoreLabels = data.map((d, i) => {
    if (!labelIndices.has(i)) return null
    const x = xScale(i)
    const y = yScale(d.score)
    const isLast = i === lastIdx
    return (
      <g key={`label-${i}`}>
        <rect x={x - 16} y={y - 22} width={32} height={17} rx={4}
          fill={isLast ? '#1677ff' : '#52c41a'} opacity={0.9} />
        <text x={x} y={y - 10} textAnchor="middle"
          fill="#fff" fontSize={11} fontWeight={600} fontFamily="ui-monospace, monospace">
          {d.score}
        </text>
      </g>
    )
  })

  return (
    <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
      <svg
        viewBox={`0 0 ${WIDTH} ${height}`}
        width="100%"
        height={height}
        style={{ display: 'block', minWidth: 320 }}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#52c41a" stopOpacity={0.25} />
            <stop offset="100%" stopColor="#52c41a" stopOpacity={0.02} />
          </linearGradient>
          <clipPath id={clipId}>
            <rect x={PAD_LEFT} y={PAD_TOP} width={chartW} height={chartH} />
          </clipPath>
        </defs>

        {/* 网格 */}
        {gridLines}

        {/* X 轴标签 */}
        {dateLabels}

        {/* 面积填充 */}
        <path d={areaPath} fill={`url(#${gradientId})`} clipPath={`url(#${clipId})`} />

        {/* 折线 */}
        <path d={linePath} fill="none" stroke="#52c41a" strokeWidth={2.5}
          strokeLinejoin="round" strokeLinecap="round" clipPath={`url(#${clipId})`} />

        {/* 数据点 */}
        {dots}

        {/* 分数标签 */}
        {scoreLabels}
      </svg>

      {/* 悬浮提示 */}
      {tooltip && (
        <div
          style={{
            position: 'fixed',
            left: tooltip.x + 12,
            top: tooltip.y - 40,
            background: 'rgba(0,0,0,0.82)',
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
            📅 {tooltip.date}  ·  <b>{tooltip.score} 分</b>
          </Text>
        </div>
      )}
    </div>
  )
}
