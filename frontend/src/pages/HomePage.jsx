import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Typography, Space, Tag, Avatar, Progress, Table, Button } from 'antd'
import {
  UserOutlined,
  BookOutlined,
  TrophyOutlined,
  RiseOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CaretUpOutlined,
  CaretDownOutlined,
  ReloadOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import { getProfile } from '../api/profile'
import { getEvaluation, getProgressStats } from '../api/evaluate'
import { formatDuration, formatDate } from '../utils/format'
import LoadingSkeleton from '../components/LoadingSkeleton'
import RadarChart from '../components/RadarChart'
import ScoreTrendChart from '../components/ScoreTrendChart'
import ProgressBar from '../components/ProgressBar'
import { deriveDimensions } from '../components/ProfileCard'

const { Title, Text } = Typography

const STUDENT_ID = 'demo-student-01'

// 知识点得分表格列定义
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
    render: (v) => {
      const colorMap = { '优秀': 'success', '良好': 'processing', '需提升': 'warning', '薄弱': 'error' }
      return <Tag color={colorMap[v] || 'default'}>{v}</Tag>
    },
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

/**
 * 首页 / 个人中心 — 融合学习评估
 *
 * 包含：欢迎横幅 | 统计卡片 | 六维画像雷达图 | 知识点得分表 | 评分趋势 | 评估历史
 */
export default function HomePage() {
  const [profile, setProfile] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [progressStats, setProgressStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [genProgress, setGenProgress] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      try {
        const [profileData, evalData, statsData] = await Promise.all([
          getProfile(STUDENT_ID).catch(() => null),
          getEvaluation(STUDENT_ID).catch(() => null),
          getProgressStats(STUDENT_ID).catch(() => null),
        ])
        if (cancelled) return

        // 画像降级 Mock
        setProfile(profileData || {
          name: '张同学',
          level: '中级',
          progress: 68,
          strengths: ['数学', '物理', '化学'],
          weaknesses: ['英语'],
          style: '实践型',
          dimensions: { knowledge: 82, ability: 70, thinking: 75, style: 72, progress: 68, goalClarity: 85 },
          topics: [
            { name: '二次函数', accuracy: 0.92 },
            { name: '力学基础', accuracy: 0.85 },
            { name: '电路分析', accuracy: 0.78 },
            { name: '英语语法', accuracy: 0.55 },
            { name: '三角函数', accuracy: 0.88 },
          ],
        })

        // 评估降级 Mock
        setEvaluation(evalData || {
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
        })

        setProgressStats(statsData || {
          totalTopics: 12,
          masteredTopics: 5,
          learningTopics: 4,
          notStartedTopics: 3,
        })
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [])

  // 模拟生成评估
  async function handleGenerate() {
    setGenerating(true)
    setGenProgress(0)
    const timer = setInterval(() => {
      setGenProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer)
          setGenerating(false)
          // 重新加载数据
          Promise.all([
            getEvaluation(STUDENT_ID).catch(() => null),
            getProgressStats(STUDENT_ID).catch(() => null),
          ]).then(([evalData, statsData]) => {
            if (evalData) setEvaluation(evalData)
            if (statsData) setProgressStats(statsData)
          })
          return 100
        }
        return Math.min(prev + Math.random() * 15, 100)
      })
    }, 500)
  }

  async function handleRefresh() {
    setLoading(true)
    try {
      const [profileData, evalData, statsData] = await Promise.all([
        getProfile(STUDENT_ID).catch(() => null),
        getEvaluation(STUDENT_ID).catch(() => null),
        getProgressStats(STUDENT_ID).catch(() => null),
      ])
      if (profileData) setProfile(profileData)
      if (evalData) setEvaluation(evalData)
      if (statsData) setProgressStats(statsData)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <LoadingSkeleton type="detail" />

  const trendArrow = evaluation?.recentTrend === 'up'
    ? <CaretUpOutlined style={{ color: '#52c41a', fontSize: 14 }} />
    : evaluation?.recentTrend === 'down'
      ? <CaretDownOutlined style={{ color: '#ff4d4f', fontSize: 14 }} />
      : null

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 24px 48px' }}>
      {/* ========== 欢迎横幅 ========== */}
      <div
        className="tech-banner"
        style={{
          position: 'relative',
          borderRadius: 16,
          padding: '24px 32px',
          marginBottom: 24,
          background: 'linear-gradient(135deg, #0f0c29 0%, #1a1040 40%, #0d1b3e 100%)',
          overflow: 'hidden',
          color: '#fff',
          boxShadow: '0 4px 32px rgba(99, 102, 241, 0.25), 0 1px 4px rgba(0, 0, 0, 0.15)',
        }}
      >
        {/* 背景光晕 */}
        <div style={{ position: 'absolute', top: -40, right: -40, width: 220, height: 220, borderRadius: '50%', background: 'radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, rgba(99, 102, 241, 0.1) 40%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: -60, left: '25%', width: 300, height: 150, borderRadius: '50%', background: 'radial-gradient(ellipse, rgba(59, 130, 246, 0.2) 0%, rgba(99, 102, 241, 0.08) 40%, transparent 70%)', pointerEvents: 'none' }} />
        <div className="tech-grid" style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)', backgroundSize: '40px 40px', pointerEvents: 'none' }} />

        <Row align="middle" gutter={[24, 16]} style={{ position: 'relative', zIndex: 1 }}>
          <Col>
            <Avatar size={72} icon={<UserOutlined />} className="tech-avatar-glow"
              style={{ backgroundColor: 'transparent', border: '2px solid rgba(139, 92, 246, 0.6)', boxShadow: '0 0 28px rgba(139, 92, 246, 0.4), inset 0 0 20px rgba(139, 92, 246, 0.12)' }} />
          </Col>
          <Col flex="auto">
            <Title level={4} style={{ margin: 0, color: '#f8f7ff', fontWeight: 600, letterSpacing: 0.5 }}>
              欢迎回来，{profile?.name || '同学'}
            </Title>
            <Space size="middle" style={{ marginTop: 6 }}>
              <Text style={{ color: 'rgba(255,255,255,0.78)' }}>{profile?.level || '--'} 级 · 学习进度 {profile?.progress ?? 0}%</Text>
              {trendArrow && <Text style={{ color: 'rgba(255,255,255,0.78)' }}>{trendArrow} {evaluation?.recentTrend === 'up' ? '持续进步中' : '继续加油'}</Text>}
            </Space>
            <br />
            <Space style={{ marginTop: 8 }}>
              {profile?.strengths?.map((s) => (
                <Tag key={s} color="purple" style={{ borderRadius: 4, background: 'rgba(139, 92, 246, 0.25)', border: '1px solid rgba(139, 92, 246, 0.45)', color: '#c4b5fd', fontWeight: 500 }}>优势: {s}</Tag>
              ))}
              {profile?.weaknesses?.map((w) => (
                <Tag key={w} style={{ borderRadius: 4, background: 'rgba(251, 191, 36, 0.18)', border: '1px solid rgba(251, 191, 36, 0.4)', color: '#fcd34d', fontWeight: 500 }}>待提升: {w}</Tag>
              ))}
            </Space>
          </Col>
          <Col>
            <Space>
              <Button ghost icon={<ReloadOutlined />} onClick={handleRefresh}>刷新</Button>
              <Button ghost icon={<DownloadOutlined />} onClick={handleGenerate} loading={generating}
                style={{ borderColor: 'rgba(139, 92, 246, 0.6)', color: '#c4b5fd' }}>
                {generating ? '生成中...' : '生成新评估'}
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* 生成进度 */}
      {generating && (
        <Card style={{ marginBottom: 24 }}>
          <ProgressBar status="running" percent={Math.min(genProgress, 100)} message="AI 正在评估你的学习情况..." />
        </Card>
      )}

      {/* ========== 统计卡片行（5 列均分占满） ========== */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        {[
          { title: '综合评分', value: evaluation?.overallScore ?? 0, suffix: '分', icon: <TrophyOutlined />, color: '#aa3bff', trend: trendArrow },
          { title: '近期趋势', value: evaluation?.recentTrend === 'up' ? '上升中 ↑' : '稳定 →', suffix: null, icon: <RiseOutlined />, color: evaluation?.recentTrend === 'up' ? '#52c41a' : '#1677ff' },
          { title: '学习进度', value: profile?.progress ?? 0, suffix: '%', icon: <RiseOutlined />, color: '#52c41a' },
          { title: '完成任务', value: evaluation?.completedTasks ?? 0, suffix: null, icon: <CheckCircleOutlined />, color: '#1677ff' },
          { title: '学习时长', value: formatDuration(evaluation?.totalTime || 0), suffix: null, icon: <ClockCircleOutlined />, color: '#fa8c16' },
        ].map((stat) => (
          <div key={stat.title} style={{ flex: '1 1 180px', minWidth: 0, display: 'flex' }}>
            <Card hoverable className="tech-stat-card"
              style={{ width: '100%', borderRadius: 12, border: '1px solid var(--border, #e5e4e7)', background: 'rgba(255,255,255,0.82)', backdropFilter: 'blur(10px)', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)' }}>
              <div style={{ position: 'absolute', left: 0, top: '15%', height: '70%', width: 3, borderRadius: '0 3px 3px 0', background: `linear-gradient(180deg, ${stat.color}, ${stat.color}cc)`, opacity: 0.8 }} />
              <Statistic
                title={<Text style={{ color: '#595959', fontSize: 13, fontWeight: 500 }}>{stat.title}</Text>}
                value={stat.value}
                suffix={<span style={{ fontSize: 14 }}>{stat.suffix} {stat.trend}</span>}
                prefix={React.cloneElement(stat.icon, { style: { color: stat.color } })}
                valueStyle={{ color: '#1a1a2e', fontWeight: 700, fontSize: 24 }}
              />
            </Card>
          </div>
        ))}
      </div>

      {/* ========== 六维画像 · 进度总览 · 评分趋势（三列并排）========== */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        {/* 六维学习画像 */}
        <Col xs={24} md={9}>
          <Card
            style={{ borderRadius: 12, border: '1px solid var(--border, #e5e4e7)', background: 'rgba(255,255,255,0.82)', backdropFilter: 'blur(10px)', boxShadow: '0 1px 3px rgba(0,0,0,0.04)', height: '100%' }}
            styles={{ body: { display: 'flex', flexDirection: 'column', alignItems: 'center' } }}
          >
            <Title level={5} style={{ color: '#1a1a2e', marginBottom: 8, textAlign: 'center' }}>
              <UserOutlined style={{ color: '#8b5cf6', marginRight: 6 }} />
              六维学习画像
            </Title>
            <RadarChart dimensions={deriveDimensions(profile)} animated size={280} />
          </Card>
        </Col>

        {/* 学习进度总览 */}
        <Col xs={24} md={6}>
          <Card
            title="学习进度总览"
            style={{ borderRadius: 12, border: '1px solid var(--border, #e5e4e7)', background: 'rgba(255,255,255,0.82)', backdropFilter: 'blur(10px)', boxShadow: '0 1px 3px rgba(0,0,0,0.04)', height: '100%' }}
          >
            {progressStats && (
              <Space direction="vertical" size="large" style={{ width: '100%', paddingTop: 8 }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <Text style={{ fontSize: 13 }}>✅ 已掌握</Text>
                    <Text strong style={{ color: '#52c41a' }}>{progressStats.masteredTopics}/{progressStats.totalTopics}</Text>
                  </div>
                  <Progress percent={Math.round((progressStats.masteredTopics / progressStats.totalTopics) * 100)} strokeColor="#52c41a" size="small" />
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <Text style={{ fontSize: 13 }}>📖 学习中</Text>
                    <Text strong style={{ color: '#1677ff' }}>{progressStats.learningTopics}/{progressStats.totalTopics}</Text>
                  </div>
                  <Progress percent={Math.round((progressStats.learningTopics / progressStats.totalTopics) * 100)} strokeColor="#1677ff" size="small" />
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <Text style={{ fontSize: 13 }}>⏳ 未开始</Text>
                    <Text strong style={{ color: '#d9d9d9' }}>{progressStats.notStartedTopics}/{progressStats.totalTopics}</Text>
                  </div>
                  <Progress percent={Math.round((progressStats.notStartedTopics / progressStats.totalTopics) * 100)} strokeColor="#d9d9d9" size="small" />
                </div>
              </Space>
            )}
          </Card>
        </Col>

        {/* 评分趋势 */}
        <Col xs={24} md={9}>
          <Card
            title="📈 评分趋势"
            style={{ borderRadius: 12, border: '1px solid var(--border, #e5e4e7)', background: 'rgba(255,255,255,0.82)', backdropFilter: 'blur(10px)', boxShadow: '0 1px 3px rgba(0,0,0,0.04)', height: '100%' }}
            styles={{ body: { padding: '12px 8px' } }}
          >
            {evaluation?.history?.length > 0 ? (
              <ScoreTrendChart data={evaluation.history} height={235} />
            ) : (
              <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>暂无趋势数据</div>
            )}
          </Card>
        </Col>
      </Row>

      {/* ========== 知识点得分明细表 ========== */}
      {evaluation?.topicScores?.length > 0 && (
        <Card title={<><TrophyOutlined style={{ color: '#aa3bff', marginRight: 8 }} />知识点得分明细</>}
          style={{ marginBottom: 24, borderRadius: 12, border: '1px solid var(--border, #e5e4e7)', background: 'rgba(255,255,255,0.82)', backdropFilter: 'blur(10px)', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <Table dataSource={evaluation.topicScores} columns={topicColumns} rowKey="topic" pagination={false} size="small" />
        </Card>
      )}

      {/* ========== 知识点掌握度 ========== */}
      {profile?.topics?.length > 0 && (
        <Card title={<><BookOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />知识点掌握度</>}
          style={{ marginBottom: 24, borderRadius: 12, border: '1px solid var(--border, #e5e4e7)', background: 'rgba(255,255,255,0.82)', backdropFilter: 'blur(10px)', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          {profile.topics.map((topic) => {
            const pct = Math.round(topic.accuracy * 100)
            return (
              <div key={topic.name} style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <Text style={{ color: '#1a1a2e', fontSize: 13, fontWeight: 500 }}>{topic.name}</Text>
                  <Text className="tech-percent" style={{ fontSize: 13, fontWeight: 600, color: pct >= 80 ? '#52c41a' : pct >= 60 ? '#fa8c16' : '#ff4d4f' }}>{pct}%</Text>
                </div>
                <Progress percent={pct} size="small" showInfo={false}
                  strokeColor={pct >= 80 ? { '0%': '#52c41a', '100%': '#73d13d' } : pct >= 60 ? { '0%': '#fa8c16', '100%': '#ffc53d' } : { '0%': '#ff4d4f', '100%': '#ff7a45' }}
                  trailColor="rgba(0,0,0,0.06)" />
              </div>
            )
          })}
        </Card>
      )}

      {/* ========== 评估历史 ========== */}
      {evaluation?.history?.length > 0 && (
        <Card title="评估历史"
          style={{ borderRadius: 12, border: '1px solid var(--border, #e5e4e7)', background: 'rgba(255,255,255,0.82)', backdropFilter: 'blur(10px)', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
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
