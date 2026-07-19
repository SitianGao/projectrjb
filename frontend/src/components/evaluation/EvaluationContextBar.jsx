import { Card, Space, Tag, Typography } from 'antd'
import { CalendarOutlined, DatabaseOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { scopeLabel, diagnosticLabel, diagnosticIcon, isAiEnhanced, confidenceText } from '../../utils/evaluationLabels'

const { Text } = Typography

function formatDate(value) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '暂无'
  return date.toLocaleString('zh-CN')
}

export default function EvaluationContextBar({ report }) {
  const evidence = report?.evidenceSummary || report?.evidence_summary || {}
  const overall = report?.overall || {}
  const courseName = report?.courseName || report?.course_name || '当前课程'
  const scopeType = report?.scopeType || report?.scope_type || report?.scope?.type
  const aiOk = isAiEnhanced(report)

  return (
    <Card className="evaluation-card context-bar" size="small">
      <div className="context-title">
        <Tag color="purple">{courseName}</Tag>
        <Text strong>{report?.stageTitle || '当前阶段'}</Text>
        <Tag>{scopeLabel(scopeType)}</Tag>
        <Tag color={aiOk ? 'purple' : 'default'}>{diagnosticIcon(report)} {diagnosticLabel(report)}</Tag>
      </div>
      <div className="context-grid">
        <span><CalendarOutlined /> 数据截止：{formatDate(report?.generatedAt || report?.created_at)}</span>
        <span><DatabaseOutlined />
          有效证据：{evidence.completed_tasks || 0} 任务 · {evidence.answered_questions || 0} 题目 · {evidence.assessments || 0} 测评 · {evidence.wrong_answers || 0} 错题
        </span>
        <span><SafetyCertificateOutlined /> 评估置信度：{confidenceText(overall.confidence)}</span>
      </div>
    </Card>
  )
}
