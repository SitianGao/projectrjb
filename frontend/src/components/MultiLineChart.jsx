import { useState, useId } from 'react'

const PAD_LEFT = 48
const PAD_RIGHT = 20
const PAD_TOP = 16
const PAD_BOTTOM = 36
const WIDTH = 700
const HEIGHT = 300

/**
 * 多系列折线图（纯 SVG）
 * @param {Array<{name: string, color: string, data: number[]}>} series
 * @param {string[]} xLabels
 */
export default function MultiLineChart({ series = [], xLabels = [], height = HEIGHT }) {
  const [tooltip, setTooltip] = useState(null)
  const clipId = useId()

  const chartW = WIDTH - PAD_LEFT - PAD_RIGHT
  const chartH = height - PAD_TOP - PAD_BOTTOM

  const allValues = series.flatMap((s) => s.data)
  const yMax = allValues.length > 0
    ? Math.max(100, Math.ceil(Math.max(...allValues) / 10) * 10)
    : 100

  const xScale = (i) => PAD_LEFT + (i / Math.max(xLabels.length - 1, 1)) * chartW
  const yScale = (v) => PAD_TOP + chartH - ((v / yMax)) * chartH

  const yTicks = Array.from({ length: 6 }, (_, i) => Math.round((yMax * i) / 5))

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <svg
        viewBox={`0 0 ${WIDTH} ${height}`}
        width="100%"
        height={height}
        style={{ display: 'block' }}
      >
        <defs>
          <clipPath id={clipId}>
            <rect x={PAD_LEFT} y={PAD_TOP - 4} width={chartW} height={chartH + 8} />
          </clipPath>
        </defs>

        {/* 网格线 */}
        {yTicks.map((tick) => (
          <g key={tick}>
            <line
              x1={PAD_LEFT} x2={WIDTH - PAD_RIGHT}
              y1={yScale(tick)} y2={yScale(tick)}
              stroke="var(--border)" strokeWidth={1} strokeDasharray="4,4"
            />
            <text x={PAD_LEFT - 8} y={yScale(tick) + 4} textAnchor="end" fill="var(--text-muted)" fontSize={11}>
              {tick}
            </text>
          </g>
        ))}

        {/* X 轴标签 */}
        {xLabels.map((label, i) => (
          <text key={i} x={xScale(i)} y={height - 10} textAnchor="middle" fill="var(--text-muted)" fontSize={11}>
            {label}
          </text>
        ))}

        {/* 折线 */}
        {series.map((s, si) => {
          const path = s.data
            .map((v, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i).toFixed(1)} ${yScale(v).toFixed(1)}`)
            .join(' ')

          return (
            <g key={si}>
              <path
                d={path} fill="none" stroke={s.color} strokeWidth={2.5}
                strokeLinejoin="round" strokeLinecap="round"
                clipPath={`url(#${clipId})`}
              />
              {s.data.map((v, i) => (
                <circle
                  key={i} cx={xScale(i)} cy={yScale(v)} r={4}
                  fill="#fff" stroke={s.color} strokeWidth={2}
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={(e) =>
                    setTooltip({ x: e.clientX, y: e.clientY, name: s.name, value: v, label: xLabels[i] })
                  }
                  onMouseLeave={() => setTooltip(null)}
                />
              ))}
            </g>
          )
        })}
      </svg>

      {/* 图例 */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 20, marginTop: 4, flexWrap: 'wrap' }}>
        {series.map((s, i) => (
          <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
            <span style={{
              width: 10, height: 10, borderRadius: 3,
              background: s.color, display: 'inline-block',
            }} />
            {s.name}
          </span>
        ))}
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: 'fixed', left: tooltip.x + 12, top: tooltip.y - 36,
          background: 'rgba(0,0,0,0.82)', color: '#fff',
          padding: '6px 12px', borderRadius: 6, fontSize: 12,
          pointerEvents: 'none', zIndex: 1000, whiteSpace: 'nowrap',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
        }}>
          <b>{tooltip.name}</b> · {tooltip.label} · {tooltip.value} 分
        </div>
      )}
    </div>
  )
}
