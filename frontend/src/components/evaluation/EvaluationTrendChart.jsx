import ReactECharts from 'echarts-for-react'
import { Card, Empty, Segmented, Statistic } from 'antd'
import { useMemo, useState } from 'react'

export default function EvaluationTrendChart({ history = [], overall }) {
  const [range, setRange] = useState('recent7')
  const rows = useMemo(() => {
    if (range === 'recent7') return history.slice(-7)
    if (range === 'all') return history
    const timestamps = history.map((row) => new Date(row.date).getTime()).filter(Number.isFinite)
    const latest = timestamps.length ? Math.max(...timestamps) : 0
    const since = latest - 30 * 86400000
    return history.filter((row) => new Date(row.date).getTime() >= since)
  }, [history, range])

  const scores = rows.map((row) => Number(row.score || 0))
  const average = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0
  const max = scores.length ? Math.max(...scores) : 0
  const min = scores.length ? Math.min(...scores) : 0
  const delta = Number(overall?.score_delta || 0)

  const option = {
    color: ['#6C5CE7'],
    tooltip: {
      trigger: 'axis',
      formatter(params) {
        const item = rows[params[0].dataIndex]
        return `${item.date}<br/>评分：${item.score} 分<br/>完成任务：${item.unique_tasks_completed || item.tasks || 0} 个<br/>答题数量：${item.questions_answered || 0} 道`
      },
    },
    grid: { left: 36, right: 24, top: 36, bottom: 32 },
    xAxis: { type: 'category', data: rows.map((row) => String(row.date).slice(5)), boundaryGap: false },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: [
      {
        type: 'line',
        smooth: true,
        data: scores,
        markLine: { symbol: 'none', data: [{ yAxis: average, name: '周期平均' }], lineStyle: { color: '#9CA3AF', type: 'dashed' } },
        markPoint: { data: scores.map((score, index) => index > 0 && score < scores[index - 1] ? { coord: [index, score], value: '降' } : null).filter(Boolean) },
        areaStyle: { color: 'rgba(108, 92, 231, 0.08)' },
      },
    ],
  }

  return (
    <Card className="evaluation-card" title="评分趋势" extra={<Segmented value={range} onChange={setRange} options={[{ label: '最近 7 次', value: 'recent7' }, { label: '最近 30 天', value: 'last30' }, { label: '全部', value: 'all' }]} />}>
      <div className="trend-stats">
        <Statistic title="本周期平均分" value={average} suffix="分" />
        <Statistic title="最高分" value={max} suffix="分" />
        <Statistic title="最低分" value={min} suffix="分" />
        <Statistic title="较上次变化" value={delta > 0 ? `+${delta}` : delta} suffix="分" />
      </div>
      {rows.length ? <ReactECharts option={option} style={{ height: 300 }} /> : <Empty description="暂无趋势数据" />}
    </Card>
  )
}
