import { Button, Table, Tag, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'
import { confidenceLabel } from '../../services/evaluationService'

const { Text } = Typography

export default function EvaluationHistoryTable({ history = [], loading }) {
  const navigate = useNavigate()
  return (
    <Table
      className="evaluation-history-table"
      loading={loading}
      dataSource={history}
      rowKey={(row) => row.evaluationId}
      columns={[
        { title: '日期', dataIndex: 'created_at', render: (v) => String(v || '').slice(0, 10) },
        { title: '课程', dataIndex: 'courseName' },
        { title: '评估范围', dataIndex: ['scope', 'type'], render: (v) => <Tag>{v || 'last_30_days'}</Tag> },
        { title: '综合评分', dataIndex: ['overall', 'score'], render: (v) => <Text strong>{v} 分</Text> },
        { title: '较上次变化', dataIndex: ['overall', 'score_delta'], render: (v) => Number(v) > 0 ? `+${v}` : v },
        {
          title: '有效数据量',
          render: (_, row) => `${row.dataSummary?.unique_tasks_completed || 0} 个任务 / ${row.dataSummary?.questions_answered || 0} 道题`,
        },
        { title: '评估置信度', dataIndex: ['overall', 'confidence'], render: confidenceLabel },
        { title: '操作', render: (_, row) => <Button type="link" onClick={() => navigate(`/assessment/report/${row.evaluationId}`)}>查看报告</Button> },
      ]}
      pagination={{ pageSize: 6 }}
    />
  )
}
