/**
 * 环形图（纯 SVG）
 * @param {Array<{label: string, value: number, color: string}>} data
 * @param {number} size - 画布尺寸
 * @param {string} centerLabel - 中心主标签
 * @param {string} centerSub - 中心副标签
 */
export default function DonutChart({ data = [], size = 200, centerLabel = '', centerSub = '' }) {
  const cx = size / 2
  const cy = size / 2
  const outerR = size / 2 - 12
  const innerR = outerR * 0.6
  const total = data.reduce((s, d) => s + d.value, 0) || 1

  let startAngle = -Math.PI / 2

  const arcs = data.map((d) => {
    const sliceAngle = (d.value / total) * Math.PI * 2
    const endAngle = startAngle + sliceAngle

    const x1 = cx + outerR * Math.cos(startAngle)
    const y1 = cy + outerR * Math.sin(startAngle)
    const x2 = cx + outerR * Math.cos(endAngle)
    const y2 = cy + outerR * Math.sin(endAngle)
    const x3 = cx + innerR * Math.cos(endAngle)
    const y3 = cy + innerR * Math.sin(endAngle)
    const x4 = cx + innerR * Math.cos(startAngle)
    const y4 = cy + innerR * Math.sin(startAngle)

    const largeArc = sliceAngle > Math.PI ? 1 : 0

    const path = [
      `M ${x1} ${y1}`,
      `A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2} ${y2}`,
      `L ${x3} ${y3}`,
      `A ${innerR} ${innerR} 0 ${largeArc} 0 ${x4} ${y4}`,
      'Z',
    ].join(' ')

    const result = { ...d, path, startAngle, endAngle }
    startAngle = endAngle
    return result
  })

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} style={{ display: 'block', margin: '0 auto' }}>
      {arcs.map((arc, i) => (
        <path key={i} d={arc.path} fill={arc.color} stroke="#fff" strokeWidth={2} />
      ))}

      {/* 中心文字 */}
      {centerLabel && (
        <text x={cx} y={cy - 6} textAnchor="middle" dominantBaseline="bottom"
          fontSize={22} fontWeight={700} fill="var(--text-primary)">
          {centerLabel}
        </text>
      )}
      {centerSub && (
        <text x={cx} y={cy + 14} textAnchor="middle" dominantBaseline="top"
          fontSize={12} fill="var(--text-muted)">
          {centerSub}
        </text>
      )}
    </svg>
  )
}
