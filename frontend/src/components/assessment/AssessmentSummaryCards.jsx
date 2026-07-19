import { Skeleton } from 'antd'
import {
  CheckCircleOutlined,
  FireOutlined,
  LineChartOutlined,
  WarningOutlined,
} from '@ant-design/icons'

const CARDS_CONFIG = [
  {
    key: 'overall_mastery',
    label: '综合掌握度',
    icon: <CheckCircleOutlined />,
    iconBg: 'rgba(108, 92, 231, 0.12)',
    iconColor: '#6C5CE7',
    suffix: '%',
    trendKey: 'mastery_change',
    trendSuffix: '%',
    trendPositive: 'up',
  },
  {
    key: 'stage_completion',
    label: '当前阶段完成度',
    icon: <FireOutlined />,
    iconBg: 'rgba(22, 119, 255, 0.1)',
    iconColor: '#1677ff',
    suffix: '%',
    trendKey: 'completion_change',
    trendSuffix: '%',
    trendPositive: 'up',
  },
  {
    key: 'latest_score',
    label: '最近测评成绩',
    icon: <LineChartOutlined />,
    iconBg: 'rgba(34, 197, 94, 0.1)',
    iconColor: '#22C55E',
    suffix: '分',
    trendKey: 'score_change',
    trendSuffix: '分',
    trendPositive: 'up',
  },
  {
    key: 'weak_knowledge_count',
    label: '待强化知识点',
    icon: <WarningOutlined />,
    iconBg: 'rgba(239, 68, 68, 0.08)',
    iconColor: '#EF4444',
    suffix: '个',
    trendKey: 'weak_change',
    trendSuffix: '',
    trendPositive: 'down', // 减少是好事
  },
]

function TrendTag({ value, suffix, positive }) {
  if (value === 0 || value === undefined || value === null) {
    return <span className="summary-card-trend neutral">持平</span>
  }
  const isUp = value > 0
  // 对于 weak_change，减少是好事
  const cls = positive === 'down'
    ? (isUp ? 'down' : 'up')
    : (isUp ? 'up' : 'down')
  const prefix = isUp ? '↑ +' : '↑ '
  // 对于减少的情况
  const display = positive === 'down'
    ? (isUp ? `↑ +${value}${suffix}` : `↓ ${value}${suffix}`)
    : (isUp ? `↑ +${value}${suffix}` : `↓ ${value}${suffix}`)

  return <span className={`summary-card-trend ${cls}`}>{display}</span>
}

export default function AssessmentSummaryCards({ overview, loading }) {
  if (loading) {
    return (
      <div className="assessment-summary-grid">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="summary-card">
            <div className="summary-card-body">
              <Skeleton active paragraph={{ rows: 2 }} />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (!overview) return null

  return (
    <div className="assessment-summary-grid">
      {CARDS_CONFIG.map((cfg) => {
        const value = overview[cfg.key]
        const trendValue = overview[cfg.trendKey]
        return (
          <div key={cfg.key} className="summary-card">
            <div className="summary-card-body">
              <div
                className="summary-card-icon"
                style={{ background: cfg.iconBg, color: cfg.iconColor }}
              >
                {cfg.icon}
              </div>
              <div className="summary-card-value">
                {value !== null && value !== undefined ? value : '—'}
                {value !== null && value !== undefined && (
                  <span style={{ fontSize: 16, fontWeight: 500, marginLeft: 2 }}>{cfg.suffix}</span>
                )}
              </div>
              <div className="summary-card-label">{cfg.label}</div>
              <TrendTag value={trendValue} suffix={cfg.trendSuffix} positive={cfg.trendPositive} />
            </div>
          </div>
        )
      })}
    </div>
  )
}
