import { Button, Card, Empty, Progress, Skeleton, Typography } from 'antd'
import {
  BookOutlined,
  EditOutlined,
  RobotOutlined,
} from '@ant-design/icons'

const { Text } = Typography

function masteryColor(mastery) {
  if (mastery >= 70) return '#fa8c16'
  if (mastery >= 50) return '#EF4444'
  return '#DC2626'
}

function WeakPointCard({ point, onReview, onPractice, onTutor }) {
  const color = masteryColor(point.mastery)
  return (
    <div className="weak-point-card">
      <div className="weak-point-header">
        <span className="weak-point-name">{point.name}</span>
        <span className="weak-point-mastery" style={{ color }}>{point.mastery}%</span>
      </div>

      <Progress
        percent={point.mastery}
        showInfo={false}
        strokeColor={color}
        trailColor="#F3F4F6"
        size="small"
        style={{ marginBottom: 14 }}
      />

      {/* 诊断依据 */}
      {point.evidence && point.evidence.length > 0 && (
        <div className="weak-point-section">
          <div className="weak-point-section-label">诊断依据</div>
          <ul className="weak-point-evidence">
            {point.evidence.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 主要问题 */}
      {point.reason && (
        <div className="weak-point-section">
          <div className="weak-point-section-label">主要问题</div>
          <div className="weak-point-suggestion">{point.reason}</div>
        </div>
      )}

      {/* 改进建议 */}
      {point.suggestions && point.suggestions.length > 0 && (
        <div className="weak-point-section">
          <div className="weak-point-section-label">改进建议</div>
          <div className="weak-point-suggestion">
            {point.suggestions.map((s, i) => (
              <div key={i} style={{ marginBottom: 2 }}>• {s}</div>
            ))}
          </div>
        </div>
      )}

      {/* 操作按钮 */}
      <div className="weak-point-actions">
        <Button
          size="small"
          type="primary"
          icon={<BookOutlined />}
          onClick={() => onReview?.(point)}
          style={{ background: '#6C5CE7', borderColor: '#6C5CE7' }}
        >
          重新学习
        </Button>
        <Button
          size="small"
          icon={<EditOutlined />}
          onClick={() => onPractice?.(point)}
        >
          专项练习
        </Button>
        <Button
          size="small"
          icon={<RobotOutlined />}
          onClick={() => onTutor?.(point)}
        >
          问AI导师
        </Button>
      </div>
    </div>
  )
}

export default function AssessmentWeakPoints({ weakPoints, loading, onReview, onPractice, onTutor }) {
  if (loading) {
    return (
      <div className="weak-points-grid">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="weak-point-card">
            <Skeleton active paragraph={{ rows: 4 }} />
          </div>
        ))}
      </div>
    )
  }

  if (!weakPoints || weakPoints.length === 0) {
    return (
      <Card className="assessment-card">
        <Empty description="暂无薄弱知识点，继续保持！" />
      </Card>
    )
  }

  return (
    <div className="weak-points-grid">
      {weakPoints.map((point) => (
        <WeakPointCard
          key={point.knowledge_point_id || point.name}
          point={point}
          onReview={onReview}
          onPractice={onPractice}
          onTutor={onTutor}
        />
      ))}
    </div>
  )
}
