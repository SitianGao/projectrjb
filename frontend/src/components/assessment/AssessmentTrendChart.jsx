import ReactECharts from 'echarts-for-react'
import { Card, Empty, Segmented, Skeleton } from 'antd'
import { useMemo, useState } from 'react'

export default function AssessmentTrendChart({ trend, loading }) {
  const [range, setRange] = useState('all')

  const data = useMemo(() => {
    if (!trend) return null
    const labels = trend.labels || []
    const scores = trend.score_series || []
    const mastery = trend.mastery_series || []
    const completion = trend.completion_series || []
    // 根据 range 切片
    const len = labels.length
    let start = 0
    if (range === 'recent5') start = Math.max(0, len - 5)
    if (range === 'recent3') start = Math.max(0, len - 3)
    return {
      labels: labels.slice(start),
      scores: scores.slice(start),
      mastery: mastery.slice(start),
      completion: completion.slice(start),
    }
  }, [trend, range])

  const option = useMemo(() => {
    if (!data) return null
    return {
      color: ['#6C5CE7', '#1677ff', '#22C55E'],
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.96)',
        borderColor: '#E5E7EB',
        textStyle: { color: '#111827', fontSize: 13 },
        formatter(params) {
          let html = `<strong>${params[0].axisValue}</strong><br/>`
          params.forEach((p) => {
            html += `${p.marker} ${p.seriesName}：<strong>${p.value}</strong><br/>`
          })
          return html
        },
      },
      legend: {
        bottom: 0,
        textStyle: { color: '#6B7280', fontSize: 12 },
        itemWidth: 16,
        itemHeight: 3,
      },
      grid: { left: 40, right: 20, top: 20, bottom: 48 },
      xAxis: {
        type: 'category',
        data: data.labels,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#E5E7EB' } },
        axisLabel: { color: '#9CA3AF', fontSize: 12 },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
        axisLabel: { color: '#9CA3AF', fontSize: 12 },
      },
      series: [
        {
          name: '测评成绩',
          type: 'line',
          smooth: true,
          data: data.scores,
          lineStyle: { width: 2.5 },
          areaStyle: { color: 'rgba(108, 92, 231, 0.06)' },
          symbolSize: 6,
        },
        {
          name: '知识掌握度',
          type: 'line',
          smooth: true,
          data: data.mastery,
          lineStyle: { width: 2.5 },
          areaStyle: { color: 'rgba(22, 119, 255, 0.04)' },
          symbolSize: 6,
        },
        {
          name: '任务完成率',
          type: 'line',
          smooth: true,
          data: data.completion,
          lineStyle: { width: 2.5 },
          areaStyle: { color: 'rgba(34, 197, 94, 0.04)' },
          symbolSize: 6,
        },
      ],
    }
  }, [data])

  const hasData = data && data.labels.length > 0

  // 计算统计值
  const avgScore = hasData ? Math.round(data.scores.reduce((a, b) => a + b, 0) / data.scores.length) : 0
  const latestMastery = hasData ? data.mastery[data.mastery.length - 1] : 0
  const latestCompletion = hasData ? data.completion[data.completion.length - 1] : 0

  if (loading) {
    return (
      <Card className="assessment-card">
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    )
  }

  return (
    <Card
      className="assessment-card"
      title={<span className="assessment-card-title">学习趋势</span>}
      extra={
        <Segmented
          value={range}
          onChange={setRange}
          size="small"
          options={[
            { label: '近3次', value: 'recent3' },
            { label: '近5次', value: 'recent5' },
            { label: '全部', value: 'all' },
          ]}
        />
      }
    >
      {hasData ? (
        <>
          <div className="trend-stats">
            <div className="trend-stat-item">
              <div className="trend-stat-label">平均成绩</div>
              <div className="trend-stat-value">{avgScore}<span style={{ fontSize: 14, fontWeight: 400 }}>分</span></div>
            </div>
            <div className="trend-stat-item">
              <div className="trend-stat-label">当前掌握度</div>
              <div className="trend-stat-value">{latestMastery}<span style={{ fontSize: 14, fontWeight: 400 }}>%</span></div>
            </div>
            <div className="trend-stat-item">
              <div className="trend-stat-label">当前完成率</div>
              <div className="trend-stat-value">{latestCompletion}<span style={{ fontSize: 14, fontWeight: 400 }}>%</span></div>
            </div>
          </div>
          <ReactECharts option={option} style={{ height: 280 }} />
        </>
      ) : (
        <Empty description="暂无趋势数据" />
      )}
    </Card>
  )
}
