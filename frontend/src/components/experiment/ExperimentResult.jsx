import { useState, useMemo } from 'react'
import { Tabs, Typography, Table, Alert, Spin, Empty, Space, Tag } from 'antd'
import {
  LineChartOutlined, ConsoleSqlOutlined, BulbOutlined,
  RobotOutlined, TableOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'

const { Text, Paragraph } = Typography

/**
 * 实验结果面板 — 展示运行输出、图表、对比、AI 分析。
 */
export default function ExperimentResult({
  result,
  loading = false,
  history = [],
  aiAnalysis = '',
  aiLoading = false,
  onAIAnalyze,
  children,
}) {
  const [activeTab, setActiveTab] = useState('console')

  if (loading) {
    return (
      <div style={{
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: 40,
        textAlign: 'center',
        background: 'var(--bg-card)',
      }}>
        <Spin tip="正在运行实验..." />
      </div>
    )
  }

  if (!result) return null

  const tabItems = [
    {
      key: 'console',
      label: <span><ConsoleSqlOutlined /> 控制台输出</span>,
      children: <ConsoleOutput result={result} />,
    },
    ...(result.chart_data?.loss_curve || result.chart_data?.accuracy_curve ? [{
      key: 'chart',
      label: <span><LineChartOutlined /> 损失曲线</span>,
      children: <ChartPanel chartData={result.chart_data} />,
    }] : []),
    ...(history.length > 1 ? [{
      key: 'compare',
      label: <span><TableOutlined /> 结果对比</span>,
      children: <CompareTable history={history} />,
    }] : []),
    {
      key: 'ai',
      label: <span><RobotOutlined /> AI 实验分析</span>,
      children: (
        <AIAnalysisPanel
          analysis={aiAnalysis}
          loading={aiLoading}
          onAnalyze={onAIAnalyze}
          result={result}
        />
      ),
    },
    {
      key: 'observations',
      label: <span><BulbOutlined /> 实验观察</span>,
      children: <ObservationsPanel result={result} />,
    },
  ]

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 8,
      overflow: 'hidden',
      background: 'var(--bg-card)',
    }}>
      {/* 状态栏 */}
      <div style={{
        padding: '8px 14px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-page)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <Space size={8}>
          <Tag color={result.status === 'success' ? 'green' : result.status === 'timeout' ? 'orange' : 'red'}>
            {result.status === 'success' ? '运行成功' :
             result.status === 'timeout' ? '执行超时' :
             result.status === 'runtime_error' ? '运行错误' :
             result.status === 'safety_error' ? '安全拦截' : result.status}
          </Tag>
          {result.execution_time_ms > 0 && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              耗时 {result.execution_time_ms.toFixed(0)}ms
            </Text>
          )}
        </Space>
        {children}
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="small"
        style={{ padding: '0 8px' }}
      />
    </div>
  )
}

/* ── 控制台输出 ── */
function ConsoleOutput({ result }) {
  const { stdout, stderr, status } = result

  return (
    <div style={{ padding: '8px 0' }}>
      {stderr && status !== 'success' && (
        <Alert
          type="error"
          message="错误信息"
          description={
            <pre style={{
              margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all',
              fontSize: 12, maxHeight: 200, overflow: 'auto',
            }}>
              {stderr}
            </pre>
          }
          style={{ marginBottom: 8 }}
          showIcon
        />
      )}
      <pre style={{
        background: '#1e1e2e',
        color: '#cdd6f4',
        padding: 14,
        borderRadius: 8,
        fontSize: 13,
        lineHeight: 1.6,
        maxHeight: 350,
        overflow: 'auto',
        margin: 0,
      }}>
        {stdout || <Text type="secondary" style={{ color: '#666' }}>（无输出）</Text>}
      </pre>
      {stderr && status === 'success' && (
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
          stderr: {stderr}
        </Text>
      )}
    </div>
  )
}

/* ── 图表面板 ── */
function ChartPanel({ chartData }) {
  const option = useMemo(() => {
    const series = []
    const legend = []

    if (chartData.loss_curve?.length > 0) {
      series.push({
        name: 'Loss',
        type: 'line',
        data: chartData.loss_curve.map((p) => [p.epoch, p.loss]),
        smooth: true,
        lineStyle: { width: 2 },
        itemStyle: { color: '#f38ba8' },
      })
      legend.push('Loss')
    }

    if (chartData.accuracy_curve?.length > 0) {
      series.push({
        name: 'Accuracy',
        type: 'line',
        yAxisIndex: chartData.loss_curve?.length > 0 ? 1 : 0,
        data: chartData.accuracy_curve.map((p) => [p.epoch, p.acc]),
        smooth: true,
        lineStyle: { width: 2 },
        itemStyle: { color: '#89b4fa' },
      })
      legend.push('Accuracy')
    }

    const yAxis = [
      {
        type: 'value',
        name: 'Loss',
        position: 'left',
        axisLabel: { formatter: '{value}' },
      },
    ]

    if (chartData.loss_curve?.length > 0 && chartData.accuracy_curve?.length > 0) {
      yAxis.push({
        type: 'value',
        name: 'Accuracy',
        position: 'right',
        min: 0,
        max: 1,
        axisLabel: { formatter: '{value}' },
      })
    }

    return {
      tooltip: { trigger: 'axis' },
      legend: { data: legend, bottom: 0 },
      grid: { top: 30, bottom: 40, left: 50, right: chartData.accuracy_curve?.length > 0 ? 50 : 20 },
      xAxis: {
        type: 'value',
        name: 'Epoch',
        axisLabel: { formatter: '{value}' },
      },
      yAxis,
      series,
    }
  }, [chartData])

  return (
    <div style={{ padding: '8px 0' }}>
      <ReactECharts option={option} style={{ height: 300 }} />
    </div>
  )
}

/* ── 结果对比表 ── */
function CompareTable({ history }) {
  const columns = [
    { title: '运行', dataIndex: 'index', key: 'index', width: 60 },
    {
      title: '参数',
      dataIndex: 'parameters',
      key: 'parameters',
      render: (params) => params ? (
        <Space size={4} wrap>
          {Object.entries(params).map(([k, v]) => (
            <Tag key={k} style={{ fontSize: 11 }}>{k}={String(v)}</Tag>
          ))}
        </Space>
      ) : '-',
    },
    {
      title: '最终 Loss',
      dataIndex: 'final_loss',
      key: 'final_loss',
      render: (v) => v != null ? v.toFixed(6) : '-',
    },
    {
      title: '准确率',
      dataIndex: 'accuracy',
      key: 'accuracy',
      render: (v) => v != null ? `${(v * 100).toFixed(1)}%` : '-',
    },
    {
      title: '耗时',
      dataIndex: 'execution_time_ms',
      key: 'time',
      render: (v) => v != null ? `${v.toFixed(0)}ms` : '-',
    },
  ]

  const data = history.map((h, i) => ({
    key: i,
    index: i + 1,
    parameters: h.parameters,
    final_loss: h.metrics?.final_loss,
    accuracy: h.metrics?.accuracy,
    execution_time_ms: h.execution_time_ms,
  }))

  return (
    <div style={{ padding: '8px 0' }}>
      <Table
        columns={columns}
        dataSource={data}
        size="small"
        pagination={false}
      />
    </div>
  )
}

/* ── AI 分析面板 ── */
function AIAnalysisPanel({ analysis, loading, onAnalyze, result }) {
  return (
    <div style={{ padding: '8px 0' }}>
      {!analysis && !loading && (
        <div style={{ textAlign: 'center', padding: 20 }}>
          <Paragraph type="secondary">
            点击下方按钮，让 AI 导师分析本次实验结果
          </Paragraph>
          <button
            onClick={onAnalyze}
            style={{
              padding: '8px 24px',
              background: '#89b4fa',
              color: '#1e1e2e',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            🤖 请求 AI 分析
          </button>
        </div>
      )}
      {loading && <Spin tip="AI 正在分析实验结果..." style={{ display: 'block', textAlign: 'center', padding: 20 }} />}
      {analysis && (
        <div style={{
          background: '#f0f5ff',
          border: '1px solid #d6e4ff',
          borderRadius: 8,
          padding: 14,
        }}>
          <Text strong style={{ display: 'block', marginBottom: 8 }}>🤖 AI 实验分析</Text>
          <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 13 }}>
            {analysis}
          </Paragraph>
        </div>
      )}
    </div>
  )
}

/* ── 观察面板 ── */
function ObservationsPanel({ result }) {
  const { observations, metrics, chart_data } = result

  return (
    <div style={{ padding: '8px 0' }}>
      {observations && observations.length > 0 ? (
        <div>
          <Text strong style={{ display: 'block', marginBottom: 8 }}>📊 自动观察</Text>
          {observations.map((obs, i) => (
            <Alert
              key={i}
              message={obs}
              type="info"
              showIcon
              icon={<BulbOutlined />}
              style={{ marginBottom: 6 }}
            />
          ))}
        </div>
      ) : (
        <Empty description="暂无自动观察结论" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}

      {metrics && Object.keys(metrics).length > 0 && (
        <div style={{ marginTop: 12 }}>
          <Text strong style={{ display: 'block', marginBottom: 8 }}>📈 指标摘要</Text>
          <Space wrap>
            {Object.entries(metrics).map(([key, value]) => (
              <Tag key={key} style={{ fontSize: 13 }}>
                {key}: {typeof value === 'number' ? value.toFixed(4) : String(value)}
              </Tag>
            ))}
          </Space>
        </div>
      )}
    </div>
  )
}
