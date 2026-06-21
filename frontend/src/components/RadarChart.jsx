import { useEffect, useRef, useState, useMemo, useId } from 'react'

// 六维定义
export const DIMENSIONS = [
  { key: 'knowledge',   label: '知识掌握',   icon: '📚', color: '#aa3bff', description: '核心知识点的掌握程度' },
  { key: 'ability',     label: '学习能力',   icon: '🧠', color: '#6366f1', description: '理解与运用新知识的能力' },
  { key: 'thinking',    label: '思维水平',   icon: '💡', color: '#52c41a', description: '批判性思维与问题解决能力' },
  { key: 'style',       label: '风格适配',   icon: '🎯', color: '#fa8c16', description: '学习风格与推荐策略的匹配度' },
  { key: 'progress',    label: '学习进度',   icon: '📈', color: '#1677ff', description: '当前阶段目标的完成进度' },
  { key: 'goalClarity', label: '目标明确',   icon: '🏆', color: '#eb2f96', description: '学习目标的清晰与规划程度' },
]

const RADAR_CENTER = 160
const RADAR_RADIUS = 100
const RADAR_LEVELS = 4
const RADAR_ANGLES = DIMENSIONS.map((_, i) => (Math.PI * 2 * i) / DIMENSIONS.length - Math.PI / 2)

function getRadarPoint(angle, value, centerX = RADAR_CENTER, centerY = RADAR_CENTER, radius = RADAR_RADIUS) {
  const r = (value / 100) * radius
  return { x: centerX + r * Math.cos(angle), y: centerY + r * Math.sin(angle) }
}

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

export default function RadarChart({ dimensions = {}, animated = true, size = 320, loading = false }) {
  const uid = useId().replace(/:/g, '')
  const gradientId = `radarGradient-${uid}`
  const glowId = `radarGlow-${uid}`

  const [animProgress, setAnimProgress] = useState(0)
  const rafRef = useRef(null)

  if (loading) {
    return (
      <div style={{ width: '100%', maxWidth: size, height: size, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto' }}>
        <div style={{
          width: size * 0.6, height: size * 0.6, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0,0,0,0.04) 0%, transparent 70%)',
          animation: 'pulse 1.5s ease-in-out infinite',
        }} />
      </div>
    )
  }

  // 当 dimensions 或 animated 变化时(重)启动画
  useEffect(() => {
    cancelAnimationFrame(rafRef.current)
    if (!animated) { setAnimProgress(1); return }
    setAnimProgress(0)
    // 等下一帧再启动，确保 animProgress=0 已生效
    const startTimer = setTimeout(() => {
      const start = performance.now()
      const duration = 800
      const tick = (now) => {
        const p = Math.min(1, (now - start) / duration)
        setAnimProgress(1 - Math.pow(1 - p, 3))
        if (p < 1) rafRef.current = requestAnimationFrame(tick)
      }
      rafRef.current = requestAnimationFrame(tick)
    }, 30)
    return () => {
      cancelAnimationFrame(rafRef.current)
      clearTimeout(startTimer)
    }
  }, [dimensions, animated])

  const animatedDims = useMemo(() => {
    const result = {}
    for (const d of DIMENSIONS) {
      result[d.key] = (dimensions[d.key] || 0) * animProgress
    }
    return result
  }, [dimensions, animProgress])

  const dataPolygon = buildPolygon(animatedDims)
  const avgScore = Math.round(Object.values(animatedDims).reduce((a, b) => a + b, 0) / DIMENSIONS.length)

  const allZero = Object.values(dimensions).every(v => v === 0 || v == null)

  return (
    <svg
      viewBox={`0 0 ${RADAR_CENTER * 2} ${RADAR_CENTER * 2}`}
      style={{ width: '100%', maxWidth: size, display: 'block', margin: '0 auto' }}
    >
      <defs>
        <radialGradient id={gradientId} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(170,59,255,0.35)" />
          <stop offset="70%" stopColor="rgba(99,102,241,0.12)" />
          <stop offset="100%" stopColor="rgba(99,102,241,0)" />
        </radialGradient>
        <filter id={glowId}>
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
        const points = RADAR_ANGLES.map((a) => `${RADAR_CENTER + r * Math.cos(a)},${RADAR_CENTER + r * Math.sin(a)}`).join(' ')
        return <polygon key={lvl} points={points} fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth="1" />
      })}

      {/* 轴线 */}
      {RADAR_ANGLES.map((a, i) => (
        <line key={i} x1={RADAR_CENTER} y1={RADAR_CENTER} x2={RADAR_CENTER + RADAR_RADIUS * Math.cos(a)} y2={RADAR_CENTER + RADAR_RADIUS * Math.sin(a)} stroke="rgba(0,0,0,0.06)" strokeWidth="1" />
      ))}

      {/* 数据填充多边形 */}
      {!allZero && (
        <polygon points={dataPolygon} fill={`url(#${gradientId})`} stroke="rgba(170,59,255,0.5)" strokeWidth="2" strokeLinejoin="round" filter={`url(#${glowId})`} />
      )}

      {/* 数据顶点 */}
      {!allZero && RADAR_ANGLES.map((a, i) => {
        const dim = DIMENSIONS[i]
        const val = animatedDims[dim.key] || 0
        const { x, y } = getRadarPoint(a, val)
        return <circle key={i} cx={x} cy={y} r="4" fill="#fff" stroke={dim.color} strokeWidth="2.5" filter={`url(#${glowId})`} />
      })}

      {/* 标签 */}
      {RADAR_ANGLES.map((a, i) => {
        const dim = DIMENSIONS[i]
        const labelR = RADAR_RADIUS + 28
        const lx = RADAR_CENTER + labelR * Math.cos(a)
        const ly = RADAR_CENTER + labelR * Math.sin(a)
        const textAnchor = lx < RADAR_CENTER - 20 ? 'end' : lx > RADAR_CENTER + 20 ? 'start' : 'middle'
        return (
          <text key={i} x={lx} y={ly} textAnchor={textAnchor} dominantBaseline="central" fontSize="12" fontWeight={600} fill="#1a1a2e">
            {dim.label}
          </text>
        )
      })}

      {/* 中心数值 */}
      <text x={RADAR_CENTER} y={RADAR_CENTER} textAnchor="middle" dominantBaseline="central" fontSize="14" fontWeight={700} fill="#aa3bff">
        {avgScore}<tspan fontSize="10" fontWeight={400}>分</tspan>
      </text>
    </svg>
  )
}
