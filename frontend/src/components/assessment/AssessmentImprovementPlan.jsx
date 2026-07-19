import { Card, Empty, Skeleton, Timeline, Typography } from 'antd'
import {
  BookOutlined,
  EditOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'

const { Text } = Typography

const TYPE_CONFIG = {
  learn: { icon: <BookOutlined />, color: '#6C5CE7', bg: 'rgba(108,92,231,0.12)' },
  practice: { icon: <EditOutlined />, color: '#1677ff', bg: 'rgba(22,119,255,0.1)' },
  test: { icon: <ExperimentOutlined />, color: '#22C55E', bg: 'rgba(34,197,94,0.1)' },
}

function groupByDay(plan = []) {
  const groups = []
  let currentDay = null
  for (const item of plan) {
    if (item.day !== currentDay) {
      currentDay = item.day
      groups.push({ day: item.day, items: [] })
    }
    groups[groups.length - 1].items.push(item)
  }
  return groups
}

export default function AssessmentImprovementPlan({ improvementPlan, loading }) {
  if (loading) {
    return (
      <Card className="assessment-card">
        <Skeleton active paragraph={{ rows: 4 }} />
      </Card>
    )
  }

  if (!improvementPlan || improvementPlan.length === 0) {
    return (
      <Card className="assessment-card" title={<span className="assessment-card-title">个性化强化计划</span>}>
        <Empty description="暂无强化计划" />
      </Card>
    )
  }

  const groups = groupByDay(improvementPlan)

  // 构建 Timeline items
  const timelineItems = groups.map((group) => ({
    label: <div className="plan-day-badge">{group.day}</div>,
    children: (
      <div>
        {group.items.map((item, i) => {
          const cfg = TYPE_CONFIG[item.type] || TYPE_CONFIG.learn
          return (
            <div key={i} className="plan-item-card">
              <div className="plan-item-left">
                <div className="plan-item-icon" style={{ background: cfg.bg, color: cfg.color }}>
                  {cfg.icon}
                </div>
                <span className="plan-item-title">{item.title}</span>
              </div>
              <span className="plan-item-duration">{item.duration}</span>
            </div>
          )
        })}
      </div>
    ),
    color: '#6C5CE7',
  }))

  return (
    <Card
      className="assessment-card"
      title={<span className="assessment-card-title">个性化强化计划</span>}
    >
      <Timeline items={timelineItems} />
    </Card>
  )
}
