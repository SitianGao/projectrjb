import { Button, Card, Progress, Space, Typography } from 'antd'
import { MessageOutlined, PartitionOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { confidenceLabel, getTrendLabel } from '../../services/evaluationService'

const { Title, Text, Paragraph } = Typography

export default function OverallDiagnosisCard({ report, onReview, onPath, onTutor }) {
  const overall = report?.overall || {}
  const delta = Number(overall.score_delta || 0)
  return (
    <Card className="evaluation-card overall-card">
      <div className="overall-score">
        <Text>综合评分</Text>
        <Title>{overall.score || 0}<small>分</small></Title>
        <Progress type="circle" percent={overall.score || 0} strokeColor="#6C5CE7" size={96} />
        <Text>当前水平：{overall.level || '基础掌握'}</Text>
        <Text>较上次：{delta > 0 ? `+${delta}` : delta} 分</Text>
        <Text>评估置信度：{confidenceLabel(overall.confidence)}</Text>
      </div>
      <div className="overall-copy">
        <Text className="section-kicker">{getTrendLabel(overall.short_term_trend)}</Text>
        <Title level={4}>EvaluateAgent 综合诊断</Title>
        <Paragraph>{report?.summary || '暂无诊断摘要。'}</Paragraph>
        <Paragraph type="secondary">
          较上次变化 {delta > 0 ? `+${delta}` : delta} 分，周期平均分 {overall.period_average || 0} 分。
        </Paragraph>
        <Space wrap>
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={onReview}>开始针对性复习</Button>
          <Button icon={<PartitionOutlined />} onClick={onPath}>查看调整后的学习路径</Button>
          <Button icon={<MessageOutlined />} onClick={onTutor}>问 AI 导师</Button>
        </Space>
      </div>
    </Card>
  )
}
