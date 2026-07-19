import { Card, Empty, Skeleton, Typography } from 'antd'
import RadarChart from '../RadarChart'

const { Text } = Typography

// 将知识掌握数据转换为 RadarChart 需要的格式
function buildRadarData(knowledgeMastery = []) {
  const colors = ['#6C5CE7', '#1677ff', '#22C55E', '#fa8c16', '#eb2f96', '#6366f1']
  const dimensions = knowledgeMastery.map((item, i) => ({
    key: item.name,
    label: item.name,
    icon: '📖',
    color: colors[i % colors.length],
    description: `${item.name}掌握度 ${item.mastery}%`,
  }))
  const values = {}
  knowledgeMastery.forEach((item) => {
    values[item.name] = item.mastery
  })
  return { dimensions, values }
}

export default function AssessmentRadarChart({ knowledgeMastery, loading }) {
  if (loading) {
    return (
      <Card className="assessment-card">
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    )
  }

  const { dimensions, values } = buildRadarData(knowledgeMastery)
  const hasData = knowledgeMastery && knowledgeMastery.length > 0

  return (
    <Card
      className="assessment-card"
      title={<span className="assessment-card-title">六维能力图</span>}
    >
      {hasData ? (
        <>
          <RadarChart
            dimensions={values}
            dimensionDefs={dimensions}
            animated
            size={400}
          />
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px 16px', marginTop: 12 }}>
            {knowledgeMastery.map((item) => (
              <Text key={item.name} style={{ fontSize: 13, color: '#6B7280' }}>
                {item.name}：<Text strong style={{ color: item.mastery >= 70 ? '#22C55E' : item.mastery >= 50 ? '#fa8c16' : '#EF4444' }}>{item.mastery}%</Text>
              </Text>
            ))}
          </div>
        </>
      ) : (
        <Empty description="暂无知识掌握数据" />
      )}
    </Card>
  )
}
