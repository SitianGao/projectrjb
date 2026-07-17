import { Tooltip } from 'antd'

/**
 * Safe progress bar that clamps values to 0-100 and prevents anomalies.
 */
export default function CourseProgress({
  completed = 0,
  total = 1,
  height = 6,
  showLabel = true,
  className = '',
}) {
  const numericTotal = Number(total)
  const safeTotal = Number.isFinite(numericTotal) ? Math.max(0, numericTotal) : 0
  const numericCompleted = Number(completed)
  const safeCompleted = safeTotal === 0
    ? 0
    : Math.max(0, Math.min(Number.isFinite(numericCompleted) ? numericCompleted : 0, safeTotal))
  const percent = safeTotal > 0 ? Math.round((safeCompleted / safeTotal) * 100) : 0

  return (
    <Tooltip title={`${safeCompleted} / ${safeTotal}`}>
      <div className={className} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {showLabel && (
          <span style={{ fontSize: 13, color: '#6B7280', whiteSpace: 'nowrap', minWidth: 42 }}>
            {percent}%
          </span>
        )}
        <div style={{
          flex: 1,
          height,
          borderRadius: height / 2,
          background: '#F3F0FF',
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${percent}%`,
            borderRadius: height / 2,
            background: `linear-gradient(90deg, #6C5CE7, #A78BFA)`,
            transition: 'width 0.4s ease',
            minWidth: percent > 0 ? height : 0,
          }} />
        </div>
        {showLabel && (
          <span style={{ fontSize: 12, color: '#9CA3AF', whiteSpace: 'nowrap' }}>
            {safeCompleted}/{safeTotal}
          </span>
        )}
      </div>
    </Tooltip>
  )
}
