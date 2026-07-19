import { Empty, Table, Tag } from 'antd'
import { useNavigate } from 'react-router-dom'
import { scopeLabel, diagnosticLabel, diagnosticIcon, isAiEnhanced, confidenceText } from '../../utils/evaluationLabels'

export default function EvaluationHistoryTable({ history = [], loading = false }) {
  const navigate = useNavigate()
  if (!loading && (!history || history.length === 0)) {
    return <Empty description="暂无评估历史" image={Empty.PRESENTED_IMAGE_SIMPLE} />
  }

  const columns = [
    { title: '日期', dataIndex: 'created_at', width: 100, render: (v) => v ? new Date(v).toLocaleDateString('zh-CN') : '—' },
    { title: '课程', dataIndex: 'courseName', width: 120, render: (v, r) => v || r.course_name || '—' },
    { title: '范围', width: 90, render: (_, r) => scopeLabel(r.scopeType || r.scope_type || r.scope?.type) },
    { title: '评分', dataIndex: 'overall_score', width: 55, align: 'center',
      render: (v, r) => { const s = v ?? r.overallScore ?? r.overall?.score; return s != null ? <strong>{s}</strong> : <Tag>不足</Tag> } },
    { title: '变化', width: 50, align: 'center',
      render: (_, r) => { const d = Number(r.overall?.score_delta || 0); if (!d) return '—'; return <span style={{color:d>0?'#52c41a':'#ff4d4f'}}>{d>0?`+${d}`:d}</span> } },
    { title: '证据', dataIndex: 'evidence_count', width: 50, align: 'center', render: (v, r) => v ?? r.evidenceCount ?? '—' },
    { title: '置信度', width: 80, align: 'center', render: (_, r) => confidenceText(r.overall?.confidence || 0) },
    { title: '来源', width: 100, render: (_, r) => <Tag color={isAiEnhanced(r)?'purple':'default'}>{diagnosticIcon(r)} {diagnosticLabel(r)}</Tag> },
    { title: '操作', width: 60, align: 'center',
      render: (_, r) => <a onClick={() => navigate(`/assessment/report/${r.evaluationId || r.report_id}`)}>查看</a> },
  ]

  return <Table dataSource={history} columns={columns} rowKey={(r) => r.evaluationId || r.report_id || r.id}
    loading={loading} size="small" pagination={history.length > 20 ? { pageSize: 20 } : false} scroll={{ x: 800 }} />
}
