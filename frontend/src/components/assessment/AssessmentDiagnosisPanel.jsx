import { Card, Empty, Progress, Skeleton, Tag, Typography } from 'antd'
import { RiseOutlined, FallOutlined } from '@ant-design/icons'

const { Text } = Typography

function MasteryTag({ mastery }) {
  if (mastery >= 80) return <Tag color="success">优秀</Tag>
  if (mastery >= 60) return <Tag color="warning">中等</Tag>
  return <Tag color="error">薄弱</Tag>
}

export default function AssessmentDiagnosisPanel({ diagnosis, loading }) {
  if (loading) {
    return (
      <Card className="assessment-card">
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    )
  }

  const strengths = diagnosis?.strengths || []
  const weaknesses = diagnosis?.weaknesses || []

  return (
    <Card
      className="assessment-card"
      title={<span className="assessment-card-title">本次学习诊断</span>}
    >
      {/* 优势知识点 */}
      <div className="diagnosis-section">
        <div className="diagnosis-section-title">
          <RiseOutlined style={{ color: '#22C55E' }} />
          优势知识点
        </div>
        {strengths.length > 0 ? strengths.map((item) => (
          <div key={item.name} className="diagnosis-item">
            <div className="diagnosis-item-info">
              <div className="diagnosis-item-name">{item.name}</div>
            </div>
            <MasteryTag mastery={item.mastery} />
            <div className="diagnosis-item-mastery" style={{ color: '#22C55E' }}>
              {item.mastery}%
            </div>
          </div>
        )) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无明显优势知识点" />}
      </div>

      {/* 薄弱知识点 */}
      <div className="diagnosis-section">
        <div className="diagnosis-section-title">
          <FallOutlined style={{ color: '#EF4444' }} />
          重点薄弱点
        </div>
        {weaknesses.length > 0 ? weaknesses.map((item) => (
          <div key={item.name} className="diagnosis-item">
            <div className="diagnosis-item-info">
              <div className="diagnosis-item-name">{item.name}</div>
              {item.reason && <div className="diagnosis-item-reason">{item.reason}</div>}
            </div>
            <MasteryTag mastery={item.mastery} />
            <div className="diagnosis-item-mastery" style={{ color: item.mastery >= 60 ? '#fa8c16' : '#EF4444' }}>
              {item.mastery}%
            </div>
          </div>
        )) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无明显薄弱知识点" />}
      </div>
    </Card>
  )
}
