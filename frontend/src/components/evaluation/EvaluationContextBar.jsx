import { Card, Space, Tag, Typography } from 'antd'
import { CalendarOutlined, DatabaseOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { confidenceLabel } from '../../services/evaluationService'

const { Text } = Typography

function formatDate(value) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '暂无'
  return date.toLocaleString()
}

export default function EvaluationContextBar({ report }) {
  const summary = report?.dataSummary || {}
  const overall = report?.overall || {}
  return (
    <Card className="evaluation-card context-bar">
      <div className="context-title">
        <Tag color="purple">{report?.courseName || '当前课程'}</Tag>
        <Text strong>{report?.stageTitle || '当前阶段'}</Text>
        <Text type="secondary">{report?.scope?.type || 'last_30_days'}</Text>
      </div>
      <div className="context-grid">
        <span><CalendarOutlined /> 数据截止：{formatDate(report?.generatedAt || report?.created_at)}</span>
        <span><DatabaseOutlined /> 基于：{summary.unique_tasks_completed || 0} 个学习任务 / {summary.questions_answered || 0} 道练习题 / {summary.tests_completed || 0} 次测评 / {summary.wrongbook_reviews || 0} 条错题复习</span>
        <span><SafetyCertificateOutlined /> 评估置信度：{confidenceLabel(overall.confidence)}</span>
      </div>
      {overall.confidence < 0.55 && (
        <Space className="low-confidence">当前评估置信度较低，建议完成更多学习任务后再次评估。</Space>
      )}
    </Card>
  )
}
