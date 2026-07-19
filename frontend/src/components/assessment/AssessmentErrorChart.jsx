import ReactECharts from 'echarts-for-react'
import { Card, Empty, Skeleton } from 'antd'
import { useMemo } from 'react'

const COLORS = ['#6C5CE7', '#1677ff', '#fa8c16', '#22C55E', '#eb2f96']

export default function AssessmentErrorChart({ errorDistribution, loading }) {
  const option = useMemo(() => {
    if (!errorDistribution || errorDistribution.length === 0) return null
    const total = errorDistribution.reduce((sum, item) => sum + item.value, 0)
    return {
      color: COLORS,
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255,255,255,0.96)',
        borderColor: '#E5E7EB',
        textStyle: { color: '#111827', fontSize: 13 },
        formatter(params) {
          return `${params.marker} ${params.name}<br/>数量：<strong>${params.value}</strong>（${params.percent}%）`
        },
      },
      legend: {
        orient: 'vertical',
        right: 16,
        top: 'center',
        textStyle: { color: '#6B7280', fontSize: 12 },
        itemWidth: 12,
        itemHeight: 12,
        itemGap: 12,
      },
      series: [
        {
          type: 'pie',
          radius: ['48%', '72%'],
          center: ['38%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
              color: '#111827',
            },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.15)',
            },
          },
          labelLine: { show: false },
          data: errorDistribution.map((item) => ({
            name: item.name,
            value: item.value,
          })),
        },
      ],
      graphic: [
        {
          type: 'text',
          left: '32%',
          top: '44%',
          style: {
            text: String(total),
            textAlign: 'center',
            fill: '#111827',
            fontSize: 28,
            fontWeight: 800,
          },
        },
        {
          type: 'text',
          left: '32%',
          top: '54%',
          style: {
            text: '总错题数',
            textAlign: 'center',
            fill: '#9CA3AF',
            fontSize: 12,
          },
        },
      ],
    }
  }, [errorDistribution])

  const hasData = errorDistribution && errorDistribution.length > 0

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
      title={<span className="assessment-card-title">错题类型分布</span>}
    >
      {hasData ? (
        <ReactECharts option={option} style={{ height: 280 }} />
      ) : (
        <Empty description="暂无错题数据" />
      )}
    </Card>
  )
}
