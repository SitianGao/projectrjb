import { Button, Card, Progress, Result, Space, Tag, Typography } from 'antd'
import { MessageOutlined, PartitionOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { diagnosticLabel, diagnosticIcon, isAiEnhanced, confidenceText, trendLabel, summarizeInsufficientReason } from '../../utils/evaluationLabels'

const { Title, Text, Paragraph } = Typography

export default function OverallDiagnosisCard({ report, onReview, onPath, onTutor }) {
  const overall = report?.overall || {}
  const score = overall.score ?? report?.overall_score ?? report?.overallScore
  const hasScore = score !== null && score !== undefined && score >= 0
  const delta = Number(overall.score_delta || 0)
  const hasSufficient = report?.hasSufficientData !== false
  const aiOk = isAiEnhanced(report)

  if (!hasSufficient) {
    return (
      <Card className="evaluation-card overall-card">
        <Result
          status="info"
          title="当前有效学习数据不足"
          subTitle={summarizeInsufficientReason(report?.insufficientReason)}
        >
          <Space wrap>
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={onReview}>开始入门诊断</Button>
            <Button icon={<MessageOutlined />} onClick={onTutor}>问 AI 导师</Button>
          </Space>
        </Result>
      </Card>
    )
  }

  return (
    <Card className="evaluation-card overall-card">
      <div className="overall-score">
        <Text>综合评分</Text>
        <Title>{hasScore ? score : '—'}{hasScore && <small>分</small>}</Title>
        {hasScore ? (
          <Progress type="circle" percent={score} strokeColor="#6C5CE7" size={96} />
        ) : (
          <Text type="secondary">暂无足够数据</Text>
        )}
        <Text>当前水平：{overall.level || '—'}</Text>
        <Text>较上次：{delta !== 0 ? (delta > 0 ? `+${delta}` : delta) : '-'} 分</Text>
        <Text>评估置信度：{confidenceText(overall.confidence)}</Text>
        <div style={{ marginTop: 8 }}>
          <Tag color={aiOk ? 'purple' : 'default'}>{diagnosticIcon(report)} {diagnosticLabel(report)}</Tag>
          {report?.generationSource === 'rule_fallback' && <Tag color="orange">AI 暂不可用</Tag>}
        </div>
      </div>
      <div className="overall-copy">
        <Text className="section-kicker">{trendLabel(overall.short_term_trend)}</Text>
        <Title level={4}>{diagnosticLabel(report)}</Title>
        <Paragraph>{report?.summary || '暂无诊断摘要。'}</Paragraph>
        {hasScore && (
          <Paragraph type="secondary">
            较上次变化 {delta > 0 ? `+${delta}` : delta} 分，周期平均分 {overall.period_average || 0} 分。
          </Paragraph>
        )}
        <Space wrap>
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={onReview}>开始针对性复习</Button>
          <Button icon={<PartitionOutlined />} onClick={onPath}>查看调整后的学习路径</Button>
          <Button icon={<MessageOutlined />} onClick={onTutor}>问 AI 导师</Button>
        </Space>
      </div>
    </Card>
  )
}
