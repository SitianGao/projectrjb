import { useState, useEffect, useMemo } from 'react'
import { Card, Typography, Space, Tag, Avatar, Button, Result, Popover, Empty } from 'antd'
import {
  UserOutlined,
  BookOutlined,
  TrophyOutlined,
  RiseOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ReloadOutlined,
  DownloadOutlined,
  ThunderboltOutlined,
  FieldTimeOutlined,
  EditOutlined,
  CloseCircleOutlined,
  IdcardOutlined,
} from '@ant-design/icons'
import { getProfile } from '../api/profile'
import { useAuth } from '../contexts/AuthContext'
import { getEvaluation, getProgressStats } from '../api/evaluate'
import LoadingSkeleton from '../components/LoadingSkeleton'
import RadarChart from '../components/RadarChart'
import MultiLineChart from '../components/MultiLineChart'
import DonutChart from '../components/DonutChart'

const { Title, Text } = Typography

// ==================== 常量 ====================

const SUBJECT_COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']

const ABILITY_DIMS = [
  { key: 'memory',     label: '记忆能力',   icon: '🧠', color: '#5470c6' },
  { key: 'understand', label: '理解能力',   icon: '💡', color: '#91cc75' },
  { key: 'apply',      label: '应用能力',   icon: '🔧', color: '#fac858' },
  { key: 'analyze',    label: '分析能力',   icon: '🔍', color: '#ee6666' },
  { key: 'evaluate',   label: '评价能力',   icon: '⚖️', color: '#73c0de' },
  { key: 'create',     label: '创造能力',   icon: '✨', color: '#8b5cf6' },
]

// ==================== 子组件 ====================

function StatCard({ title, value, icon, color, suffix }) {
  return (
    <Card
      hoverable
      style={{
        flex: '1 1 160px', minWidth: 0, borderRadius: 10,
        border: '1px solid var(--border)', background: 'var(--bg-card)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)', overflow: 'hidden', position: 'relative',
        transition: 'transform 0.25s, box-shadow 0.25s, border-color 0.25s',
      }}
    >
      <div style={{
        position: 'absolute', left: 0, top: '15%', height: '70%', width: 3,
        borderRadius: '0 3px 3px 0', background: color, opacity: 0.8,
      }} />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <Text style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{title}</Text>
          <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3 }}>
            {value}{suffix && <span style={{ fontSize: 14, fontWeight: 400, color: 'var(--text-secondary)' }}>{suffix}</span>}
          </div>
        </div>
        <div style={{
          width: 44, height: 44, borderRadius: 10,
          background: `${color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {icon}
        </div>
      </div>
    </Card>
  )
}

function CognitiveBar({ name, score, color }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <Text style={{ fontSize: 13, color: 'var(--text-primary)' }}>{name}</Text>
        <Text strong style={{ fontSize: 13, color }}>{score}</Text>
      </div>
      <div style={{ height: 8, borderRadius: 4, background: 'var(--surface-secondary)', overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${Math.min(score, 100)}%`, borderRadius: 4,
          background: `linear-gradient(90deg, ${color}, ${color}cc)`,
          transition: 'width 0.8s cubic-bezier(0.25, 0.8, 0.25, 1.2)',
        }} />
      </div>
    </div>
  )
}

// ==================== 数据转换工具 ====================

/** 从 topics 数组构建知识趋势折线数据 */
function buildKnowledgeTrend(topics) {
  if (!topics || topics.length === 0) return { xLabels: [], series: [] }
  return {
    xLabels: topics[0]?.history?.map((_, i) => `第${i + 1}次`) || [],
    series: topics.map((t, i) => ({
      name: t.name,
      color: SUBJECT_COLORS[i % SUBJECT_COLORS.length],
      data: t.history || [t.accuracy ? Math.round(t.accuracy * 100) : 0],
    })),
  }
}

/** 从 topics 构建认知能力数据 */
function buildCognitiveData(topics) {
  if (!topics || topics.length === 0) return []
  return topics.map((t, i) => ({
    name: t.name,
    score: t.accuracy ? Math.round(t.accuracy * 100) : 0,
    color: SUBJECT_COLORS[i % SUBJECT_COLORS.length],
  }))
}

/** 从 topics 构建学习时长分布 */
function buildTimeDist(topics) {
  if (!topics || topics.length === 0) return []
  const maxHours = Math.max(...topics.map((t) => t.studyHours || 0), 1)
  return topics.map((t, i) => ({
    label: t.name,
    hours: t.studyHours || 0,
    maxHours,
    color: SUBJECT_COLORS[i % SUBJECT_COLORS.length],
  }))
}

/** 从 evaluation 构建答题情况 */
function buildAnswerStats(evaluation) {
  if (!evaluation) return []
  const correct = evaluation.correctRate != null ? Math.round(evaluation.correctRate * 100) : 0
  return [
    { label: '正确', value: correct, color: '#00b894' },
    { label: '错误', value: 100 - correct, color: '#fab1a0' },
  ]
}

// ==================== 主组件 ====================

export default function HomePage() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [progressStats, setProgressStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [introVisible, setIntroVisible] = useState(false)

  const studentId = user?.id || user?.student_id || ''

  useEffect(() => {
    let cancelled = false
    if (!studentId) {
      setLoading(false)
      return
    }

    async function load() {
      setError(null)
      setLoading(true)
      try {
        const [profileData, evalData, statsData] = await Promise.all([
          getProfile(studentId).catch(() => null),
          getEvaluation(studentId).catch(() => null),
          getProgressStats(studentId).catch(() => null),
        ])
        if (cancelled) return

        setProfile(profileData)
        setEvaluation(evalData)
        setProgressStats(statsData)

        if (!profileData && !evalData && !statsData) {
          setError('无法连接到后端服务，请检查网络连接后重试')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [studentId])

  async function handleRefresh() {
    setLoading(true)
    try {
      const [profileData, evalData, statsData] = await Promise.all([
        getProfile(studentId).catch(() => null),
        getEvaluation(studentId).catch(() => null),
        getProgressStats(studentId).catch(() => null),
      ])
      if (profileData) setProfile(profileData)
      if (evalData) setEvaluation(evalData)
      if (statsData) setProgressStats(statsData)
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerate() {
    try {
      const data = await getEvaluation(studentId)
      setEvaluation(data)
      const stats = await getProgressStats(studentId)
      if (stats) setProgressStats(stats)
    } catch {
      // 静默失败
    }
  }

  // ---------- 从 API 数据计算展示值 ----------
  const displayData = useMemo(() => {
    const topics = profile?.topics || []
    return {
      knowledgeTrend: buildKnowledgeTrend(topics),
      cognitiveData: buildCognitiveData(topics),
      timeDist: buildTimeDist(topics),
      answerStats: buildAnswerStats(evaluation),
    }
  }, [profile, evaluation])

  // 能力评估雷达图数据（从 profile.dimensions 映射）
  const abilityData = useMemo(() => {
    const dims = profile?.dimensions || {}
    return {
      memory: dims.memory || dims.knowledge || 0,
      understand: dims.understand || dims.ability || 0,
      apply: dims.apply || dims.thinking || 0,
      analyze: dims.analyze || dims.style || 0,
      evaluate: dims.evaluate || dims.progress || 0,
      create: dims.create || dims.goalClarity || 0,
    }
  }, [profile])

  // 学习建议（从 evaluation）
  const suggestions = evaluation?.suggestions || []

  // 统计数值
  const totalTimeHours = evaluation?.totalTime ? Math.round(evaluation.totalTime / 3600) : 0
  const overallScore = evaluation?.overallScore || 0
  const completedTasks = evaluation?.completedTasks || 0
  const totalTopics = progressStats?.totalTopics || (profile?.topics?.length || 0)
  const masteredTopics = progressStats?.masteredTopics || 0

  if (loading) return <LoadingSkeleton type="detail" />

  if (error) {
    return (
      <div style={{ maxWidth: 600, margin: '60px auto', padding: 24 }}>
        <Result
          status="error" title="加载失败" subTitle={error}
          extra={
            <Space>
              <Button type="primary" icon={<ReloadOutlined />} onClick={handleRefresh}>重新加载</Button>
              <Button icon={<DownloadOutlined />} onClick={handleGenerate}>生成新评估</Button>
            </Space>
          }
        />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', padding: '20px 24px 48px' }}>
      {/* ========== 页面标题 ========== */}
      <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* 个人介绍弹窗 */}
          <Popover
            content={
              <div style={{ maxWidth: 300, padding: '8px 4px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
                  <Avatar size={56} icon={<UserOutlined />} src={user?.avatar}
                    style={{
                      border: '2px solid rgba(139,92,246,0.5)',
                      boxShadow: '0 0 16px rgba(139,92,246,0.25)',
                      backgroundColor: '#1677ff', flexShrink: 0,
                    }} />
                  <div>
                    <Text strong style={{ fontSize: 16, color: 'var(--text-primary)' }}>
                      {profile?.name || user?.name || user?.username || '同学'}
                    </Text>
                    <br />
                    <Tag color="purple" style={{ marginTop: 4, borderRadius: 4 }}>
                      {profile?.level || '新手'} 学者
                    </Tag>
                  </div>
                </div>

                <div style={{
                  background: 'linear-gradient(135deg, rgba(139,92,246,0.06) 0%, rgba(99,102,241,0.04) 100%)',
                  borderRadius: 8, padding: '12px 14px', marginBottom: 14,
                  border: '1px solid rgba(139,92,246,0.12)',
                }}>
                  <Text style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                    {user?.bio || '这个同学很懒，还没有填写个人简介~'}
                  </Text>
                </div>

                <div style={{ display: 'flex', gap: 8 }}>
                  {[
                    { label: '掌握专题', value: masteredTopics, color: '#8b5cf6' },
                    { label: '完成任务', value: completedTasks, color: '#00b894' },
                    { label: '综合评分', value: `${overallScore}分`, color: '#0984e3' },
                  ].map((stat) => (
                    <div key={stat.label} style={{
                      flex: 1, textAlign: 'center', padding: '8px 4px',
                      background: `${stat.color}08`, borderRadius: 8,
                      border: `1px solid ${stat.color}18`,
                    }}>
                      <Text strong style={{ fontSize: 18, color: stat.color, display: 'block' }}>
                        {stat.value}
                      </Text>
                      <Text style={{ fontSize: 11, color: 'var(--text-muted)' }}>{stat.label}</Text>
                    </div>
                  ))}
                </div>

                <div style={{ marginTop: 14 }}>
                  <Text style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    🎯 学习风格：{profile?.style || '未评估'}
                  </Text>
                  {profile?.strengths?.length > 0 && (
                    <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {profile.strengths.map((s) => (
                        <Tag key={s} color="purple" style={{ borderRadius: 4, margin: 0, fontSize: 11 }}>
                          👍 {s}
                        </Tag>
                      ))}
                      {profile?.weaknesses?.map((w) => (
                        <Tag key={w} color="gold" style={{ borderRadius: 4, margin: 0, fontSize: 11 }}>
                          💪 {w}
                        </Tag>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            }
            title={null}
            trigger="click"
            open={introVisible}
            onOpenChange={setIntroVisible}
            placement="bottomLeft"
            overlayStyle={{ maxWidth: 340 }}
          >
            <div
              style={{
                display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer',
                userSelect: 'none', padding: '4px 10px', borderRadius: 8,
                background: introVisible ? 'rgba(139,92,246,0.08)' : 'transparent',
                transition: 'background 0.2s',
              }}
              onClick={(e) => { e.stopPropagation(); setIntroVisible(!introVisible) }}
            >
              <Avatar size={32} icon={<UserOutlined />} src={user?.avatar}
                style={{ backgroundColor: '#1677ff', flexShrink: 0 }} />
              <div>
                <Text strong style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.1, display: 'block' }}>
                  {profile?.name || user?.name || user?.username || '同学'}
                </Text>
                <Text style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  <IdcardOutlined style={{ marginRight: 4 }} />个人介绍
                </Text>
              </div>
            </div>
          </Popover>

          <RiseOutlined style={{ fontSize: 22, color: '#8b5cf6' }} />
          <Title level={4} style={{ margin: 0 }}>学习数据</Title>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>刷新</Button>
          <Button type="primary" icon={<DownloadOutlined />} onClick={handleGenerate}
            style={{ borderRadius: 6 }}>
            生成新评估
          </Button>
        </Space>
      </div>

      {/* ========== 主内容 + 右侧面板 ========== */}
      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        {/* ===== 左侧主内容区 ===== */}
        <div style={{ flex: '1 1 600px', minWidth: 0, display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* ---------- 统计卡片 ---------- */}
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <StatCard title="学习次数" value={completedTasks}
              icon={<ThunderboltOutlined style={{ color: '#8b5cf6', fontSize: 20 }} />} color="#8b5cf6" />
            <StatCard title="学习时长" value={totalTimeHours} suffix="h"
              icon={<FieldTimeOutlined style={{ color: '#00b894', fontSize: 20 }} />} color="#00b894" />
            <StatCard title="掌握专题" value={masteredTopics}
              icon={<EditOutlined style={{ color: '#0984e3', fontSize: 20 }} />} color="#0984e3" />
            <StatCard title="待学习" value={totalTopics - masteredTopics}
              icon={<CloseCircleOutlined style={{ color: '#e17055', fontSize: 20 }} />} color="#e17055" />
          </div>

          {/* ---------- 知识掌握变化 ---------- */}
          <Card
            title={<><RiseOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />知识掌握变化</>}
            style={{ borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg-card)' }}
          >
            {displayData.knowledgeTrend.series.length > 0 ? (
              <MultiLineChart series={displayData.knowledgeTrend.series} xLabels={displayData.knowledgeTrend.xLabels} />
            ) : (
              <Empty description="暂无知识掌握数据" />
            )}
          </Card>

          {/* ---------- 能力评估 + 认知能力评估 ---------- */}
          <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 320px', minWidth: 300 }}>
              <Card
                title={<><TrophyOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />能力评估</>}
                style={{ borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg-card)', height: '100%' }}
                styles={{ body: { display: 'flex', justifyContent: 'center' } }}
              >
                <RadarChart dimensionDefs={ABILITY_DIMS} dimensions={abilityData} size={280} />
              </Card>
            </div>

            <div style={{ flex: '1 1 300px', minWidth: 280 }}>
              <Card
                title={<><CheckCircleOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />认知能力评估</>}
                style={{ borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg-card)', height: '100%' }}
              >
                {displayData.cognitiveData.length > 0 ? (
                  displayData.cognitiveData.map((item) => (
                    <CognitiveBar key={item.name} name={item.name} score={item.score} color={item.color} />
                  ))
                ) : (
                  <Empty description="暂无认知评估数据" />
                )}
              </Card>
            </div>
          </div>

          {/* ---------- 学习建议 ---------- */}
          <Card
            title={<><BookOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />学习建议</>}
            style={{ borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg-card)' }}
          >
            {suggestions.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {suggestions.map((s, idx) => (
                  <div key={s.id || idx} style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%',
                      background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
                      color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 13, fontWeight: 700, flexShrink: 0, marginTop: 2,
                    }}>
                      {idx + 1}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <Text strong style={{ fontSize: 14, color: 'var(--text-primary)' }}>{s.title}</Text>
                        {s.tag && <Tag color={s.tagColor || 'purple'} style={{ borderRadius: 4, fontSize: 11, lineHeight: '18px' }}>{s.tag}</Tag>}
                      </div>
                      <Text style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                        {s.content}
                      </Text>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <Empty description="暂无学习建议" />
            )}
          </Card>
        </div>

        {/* ===== 右侧面板 ===== */}
        <div style={{ width: 300, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* 用户卡片 */}
          <Card
            style={{
              borderRadius: 10, border: '1px solid var(--border)',
              background: 'var(--bg-card)', overflow: 'hidden', padding: 0,
            }}
            styles={{ body: { padding: 0 } }}
          >
            <div style={{
              background: 'linear-gradient(135deg, #1a1040 0%, #0d1b3e 100%)',
              padding: '24px 20px 20px', textAlign: 'center', position: 'relative',
            }}>
              <div style={{
                position: 'absolute', top: -30, right: -30, width: 100, height: 100,
                borderRadius: '50%', background: 'radial-gradient(circle, rgba(139,92,246,0.3) 0%, transparent 70%)',
              }} />
              <Avatar size={72} icon={<UserOutlined />} src={user?.avatar}
                style={{
                  border: '3px solid rgba(139,92,246,0.6)',
                  boxShadow: '0 0 20px rgba(139,92,246,0.3)',
                  backgroundColor: 'transparent',
                }} />
              <Title level={5} style={{ color: '#f8f7ff', margin: '12px 0 4px' }}>
                {profile?.name || user?.name || user?.username || '同学'}
              </Title>
              <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13 }}>
                {profile?.level || '新手'} 学者 · {profile?.style || '未评估'}
              </Text>
            </div>
            <div style={{ padding: '16px 20px' }}>
              <Text style={{ fontSize: 13, color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                "学而不思则罔，思而不学则殆"
              </Text>
              <div style={{ marginTop: 12, display: 'flex', gap: 16 }}>
                <div style={{ textAlign: 'center', flex: 1 }}>
                  <Text strong style={{ fontSize: 18, color: '#8b5cf6' }}>{masteredTopics}</Text>
                  <br /><Text style={{ fontSize: 11, color: 'var(--text-muted)' }}>掌握专题</Text>
                </div>
                <div style={{ textAlign: 'center', flex: 1 }}>
                  <Text strong style={{ fontSize: 18, color: '#00b894' }}>{completedTasks}</Text>
                  <br /><Text style={{ fontSize: 11, color: 'var(--text-muted)' }}>完成任务</Text>
                </div>
                <div style={{ textAlign: 'center', flex: 1 }}>
                  <Text strong style={{ fontSize: 18, color: '#0984e3' }}>{overallScore}</Text>
                  <br /><Text style={{ fontSize: 11, color: 'var(--text-muted)' }}>综合评分</Text>
                </div>
              </div>
            </div>
          </Card>

          {/* 答题情况 — 环形图 */}
          <Card
            title="答题情况"
            style={{ borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg-card)' }}
            styles={{ body: { display: 'flex', flexDirection: 'column', alignItems: 'center' } }}
          >
            {displayData.answerStats.length > 0 ? (
              <>
                <DonutChart data={displayData.answerStats} size={180}
                  centerLabel={`${displayData.answerStats[0]?.value || 0}%`} centerSub="正确率" />
                <div style={{ display: 'flex', gap: 20, marginTop: 8 }}>
                  {displayData.answerStats.map((d) => (
                    <span key={d.label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
                      <span style={{ width: 10, height: 10, borderRadius: 3, background: d.color, display: 'inline-block' }} />
                      {d.label} {d.value}%
                    </span>
                  ))}
                </div>
              </>
            ) : (
              <Empty description="暂无答题数据" />
            )}
          </Card>

          {/* 学习时长分布 */}
          <Card
            title={<><ClockCircleOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />学习时长分布</>}
            style={{ borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg-card)' }}
          >
            {displayData.timeDist.length > 0 ? (
              displayData.timeDist.map((d) => (
                <div key={d.label} style={{ marginBottom: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <Text style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{d.label}</Text>
                    <Text strong style={{ fontSize: 12, color: 'var(--text-primary)' }}>{d.hours}h</Text>
                  </div>
                  <div style={{ height: 6, borderRadius: 3, background: 'var(--surface-secondary)', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: `${d.maxHours > 0 ? (d.hours / d.maxHours) * 100 : 0}%`,
                      borderRadius: 3,
                      background: d.color,
                      transition: 'width 0.6s ease',
                    }} />
                  </div>
                </div>
              ))
            ) : (
              <Empty description="暂无学习时长数据" />
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
