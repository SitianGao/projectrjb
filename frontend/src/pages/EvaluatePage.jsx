import { useState, useEffect } from 'react'
import { Row, Col, Typography, Card, Statistic, Progress, Table, Tag, Space, Button } from 'antd'
import {
  TrophyOutlined,
  RiseOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ReloadOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import MermaidChart from '../components/MermaidChart'
import ProgressBar from '../components/ProgressBar'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { getEvaluation, getProgressStats } from '../api/evaluate'
import { formatPercent, formatDuration, formatDate } from '../utils/format'
import { shouldUseMock } from '../utils/useMock'

const USE_MOCK = shouldUseMock()

const { Title, Text } = Typography

/**
 * 学习评估页 — 进度统计 + 评分图表 + 评估历史
 */
export default function EvaluatePage() {
  const [evaluation, setEvaluation] = useState(null)
  const [progressStats, setProgressStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [genProgress, setGenProgress] = useState(0)

  const studentId = 'demo-student-01'

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [evalData, statsData] = await Promise.all([
        getEvaluation(studentId).catch(() => null),
        getProgressStats(studentId).catch(() => null),
      ])
      setEvaluation(evalData || (USE_MOCK ? {
        overallScore: 78,
        recentTrend: 'up',
        completedTasks: 24,
        totalTime: 129600,
        topicScores: [
          { topic: '二次函数', score: 85, level: '优秀' },
          { topic: '力学基础', score: 72, level: '良好' },
          { topic: '电路分析', score: 60, level: '需提升' },
          { topic: '英语语法', score: 68, level: '良好' },
        ],
        history: [
          { date: '2026-06-01', score: 72, tasks: 3 },
          { date: '2026-06-02', score: 74, tasks: 2 },
          { date: '2026-06-03', score: 73, tasks: 4 },
          { date: '2026-06-04', score: 76, tasks: 3 },
          { date: '2026-06-05', score: 75, tasks: 5 },
          { date: '2026-06-06', score: 77, tasks: 4 },
          { date: '2026-06-07', score: 78, tasks: 3 },
        ],
      } : null))
      setProgressStats(statsData || (USE_MOCK ? {
        totalTopics: 12,
        masteredTopics: 5,
        learningTopics: 4,
        notStartedTopics: 3,
      } : null))
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerate() {
    if (!USE_MOCK) {
      try {
        const data = await getEvaluation(studentId)
        if (data) setEvaluation(data)
        const stats = await getProgressStats(studentId)
        if (stats) setProgressStats(stats)
        message.success('评估已刷新')
      } catch (err) {
        message.error('获取评估失败: ' + (err.message || '未知错误'))
      }
      return
    }

    // Mock 模式：模拟生成进度
    setGenerating(true)
    setGenProgress(0)
    const timer = setInterval(() => {
      setGenProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer)
          setGenerating(false)
          loadData()
          return 100
        }
        return prev + Math.random() * 15
      })
    }, 500)
  }

  const levelColorMap = {
    优秀: 'success',
    良好: 'processing',
    需提升: 'warning',
    薄弱: 'error',
  }

  const topicColumns = [
    { title: '知识点', dataIndex: 'topic', key: 'topic' },
    {
      title: '得分',
      dataIndex: 'score',
      key: 'score',
      render: (v) => <Text strong>{v}</Text>,
      sorter: (a, b) => a.score - b.score,
    },
    {
      title: '掌握程度',
      dataIndex: 'level',
      key: 'level',
      render: (v) => <Tag color={levelColorMap[v] || 'default'}>{v}</Tag>,
    },
    {
      title: '进度',
      dataIndex: 'score',
      key: 'progress',
      render: (v) => (
        <Progress
          percent={v}
          size="small"
          strokeColor={v >= 80 ? '#52c41a' : v >= 60 ? '#faad14' : '#ff4d4f'}
        />
      ),
    },
  ]

  if (loading) return <LoadingSkeleton type="detail" />

  // 构造趋势图
  const trendChart = evaluation?.history?.length
    ? `graph LR\n${evaluation.history.map((h, i) => {
        const next = evaluation.history[i + 1]
        const trend = next ? (next.score >= h.score ? '↑' : '↓') : ''
        return `  D${i}["${h.date.slice(5)}<br/>${h.score}分"]${next ? ` -->|${trend}| D${i + 1}` : ''}`
      }).join('\n')}\n  classDef up fill:#f6ffed,stroke:#52c41a\n  classDef down fill:#fff2f0,stroke:#ff4d4f`
    : ''

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0 }}>学习评估</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={handleGenerate}
            loading={generating}
          >
            生成新评估
          </Button>
        </Space>
      </div>

      {/* 生成进度 */}
      {generating && (
        <Card style={{ marginTop: 16 }}>
          <ProgressBar
            status="running"
            percent={Math.min(genProgress, 100)}
            message="AI 正在评估你的学习情况..."
          />
        </Card>
      )}

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="综合评分"
              value={evaluation?.overallScore || 0}
              suffix="分"
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="近期趋势"
              value={evaluation?.recentTrend === 'up' ? '上升中 ↑' : '稳定 →'}
              prefix={<RiseOutlined />}
              valueStyle={{ color: evaluation?.recentTrend === 'up' ? '#52c41a' : '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="完成任务"
              value={evaluation?.completedTasks || 0}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="学习时长"
              value={formatDuration(evaluation?.totalTime || 0)}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 知识点得分表 + 趋势图 */}
      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={14}>
          <Card title="知识点得分明细">
            <Table
              dataSource={evaluation?.topicScores || []}
              columns={topicColumns}
              rowKey="topic"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="学习进度总览">
            {progressStats && (
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text>已掌握 ({progressStats.masteredTopics}/{progressStats.totalTopics})</Text>
                  <Progress
                    percent={Math.round((progressStats.masteredTopics / progressStats.totalTopics) * 100)}
                    strokeColor="#52c41a"
                  />
                </div>
                <div>
                  <Text>学习中 ({progressStats.learningTopics}/{progressStats.totalTopics})</Text>
                  <Progress
                    percent={Math.round((progressStats.learningTopics / progressStats.totalTopics) * 100)}
                    strokeColor="#1677ff"
                  />
                </div>
                <div>
                  <Text>未开始 ({progressStats.notStartedTopics}/{progressStats.totalTopics})</Text>
                  <Progress
                    percent={Math.round((progressStats.notStartedTopics / progressStats.totalTopics) * 100)}
                    strokeColor="#d9d9d9"
                  />
                </div>
              </Space>
            )}
          </Card>
        </Col>
      </Row>

      {/* 评分趋势图 */}
      {trendChart && (
        <Card title="评分趋势" style={{ marginTop: 24 }}>
          <MermaidChart chart={trendChart} theme="default" />
        </Card>
      )}

      {/* 评估历史 */}
      {evaluation?.history?.length > 0 && (
        <Card title="评估历史" style={{ marginTop: 24 }}>
          <Table
            dataSource={evaluation.history}
            columns={[
              { title: '日期', dataIndex: 'date', key: 'date', render: (v) => formatDate(v, 'YYYY-MM-DD') },
              { title: '评分', dataIndex: 'score', key: 'score', render: (v) => <Text strong>{v} 分</Text> },
              { title: '完成任务', dataIndex: 'tasks', key: 'tasks', render: (v) => `${v} 个` },
            ]}
            rowKey="date"
            pagination={false}
            size="small"
          />
        </Card>
      )}
    </div>
  )
}
