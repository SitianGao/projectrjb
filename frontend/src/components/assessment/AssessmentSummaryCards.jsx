import { Skeleton } from 'antd'
import {
  CheckCircleOutlined,
  FireOutlined,
  LineChartOutlined,
  WarningOutlined,
} from '@ant-design/icons'

const ITEMS = [
  {
    key: 'overall_mastery',
    label: '综合掌握度',
    icon: <CheckCircleOutlined />,
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
    iconColor: '#EF4444',
    suffix: '个',
    trendKey: 'weak_change',
    trendSuffix: '',
    trendPositive: 'down',
  },
]

function TrendTag({ value, suffix, positive }) {
  if (value === 0 || value === undefined || value === null) {
    return <span className="summary-card-trend neutral">持平</span>
  }
  const isUp = value > 0
  const cls = positive === 'down'
    ? (isUp ? 'down' : 'up')
    : (isUp ? 'up' : 'down')
  const display = positive === 'down'
    ? (isUp ? `↑ +${value}${suffix}` : `↓ ${value}${suffix}`)
    : (isUp ? `↑ +${value}${suffix}` : `↓ ${value}${suffix}`)

  return <span className={`summary-card-trend ${cls}`}>{display}</span>
}

export default function AssessmentSummaryCards({ overview, loading }) {
  if (loading) {
    return (
      <div className="summary-card" style={{ marginBottom: 22 }}>
        <Skeleton active paragraph={{ rows: 2 }} />
      </div>
    )
  }

  if (!overview) return null

  return (
    <div className="summary-card" style={{ marginBottom: 22 }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        gap: 16,
        flexWrap: 'wrap',
      }}>
        {ITEMS.map((cfg, idx) => {
          const value = overview[cfg.key]
          const trendValue = overview[cfg.trendKey]
          return (
            <div key={cfg.key} style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              flex: '1 1 0',
              minWidth: 160,
              padding: '8px 0',
              borderRight: idx < ITEMS.length - 1 ? '1px solid var(--border)' : 'none',
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: `${cfg.iconColor}14`, color: cfg.iconColor, fontSize: 18, flexShrink: 0,
              }}>
                {cfg.icon}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, color: '#6B7280', marginBottom: 2 }}>{cfg.label}</div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
                  <span style={{ fontSize: 22, fontWeight: 700, color: '#111827' }}>
                    {value !== null && value !== undefined ? value : '—'}
                    {value !== null && value !== undefined && (
                      <span style={{ fontSize: 14, fontWeight: 500 }}>{cfg.suffix}</span>
                    )}
                  </span>
                  <TrendTag value={trendValue} suffix={cfg.trendSuffix} positive={cfg.trendPositive} />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
