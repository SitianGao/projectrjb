import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Typography, Space, Tag, Avatar, Progress } from 'antd'
import {
  UserOutlined,
  BookOutlined,
  TrophyOutlined,
  RiseOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CaretUpOutlined,
  CaretDownOutlined,
} from '@ant-design/icons'
import { getProfile } from '../api/profile'
import { getEvaluation } from '../api/evaluate'
import LoadingSkeleton from '../components/LoadingSkeleton'
import RadarChart from '../components/RadarChart'
import { deriveDimensions } from '../components/ProfileCard'

const { Title, Text } = Typography

/**
 * 首页 / 个人中心
 *
 * 展示学生概况：画像摘要、学习进度、最近路径、快捷入口
 */
export default function HomePage() {
  const [profile, setProfile] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      try {
        const [profileData, evalData] = await Promise.all([
          getProfile('demo-student-01').catch(() => null),
          getEvaluation('demo-student-01').catch(() => null),
        ])
        if (!cancelled) {
          setProfile(profileData)
          setEvaluation(evalData)
        }
      } catch {
        if (!cancelled) {
          setProfile({
            name: '张同学',
            level: '中级',
            progress: 68,
            strengths: ['数学', '物理', '化学'],
            weaknesses: ['英语'],
            style: '实践型',
            dimensions: {
              knowledge: 82,
              ability: 70,
              thinking: 75,
              style: 72,
              progress: 68,
              goalClarity: 85,
            },
            topics: [
              { name: '二次函数', accuracy: 0.92 },
              { name: '力学基础', accuracy: 0.85 },
              { name: '电路分析', accuracy: 0.78 },
              { name: '英语语法', accuracy: 0.55 },
              { name: '三角函数', accuracy: 0.88 },
            ],
          })
          setEvaluation({
            overallScore: 78,
            recentTrend: 'up',
            completedTasks: 24,
            totalHours: 36,
          })
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [])

  if (loading) return <LoadingSkeleton type="detail" />

  /** 趋势箭头 */
  const trendArrow = evaluation?.recentTrend === 'up'
    ? <CaretUpOutlined style={{ color: '#52c41a', fontSize: 14 }} />
    : evaluation?.recentTrend === 'down'
      ? <CaretDownOutlined style={{ color: '#ff4d4f', fontSize: 14 }} />
      : null

  return (
    <div>
      {/* ========== 欢迎横幅 — 深色科技渐变 ========== */}
      <div
        className="tech-banner"
        style={{
          position: 'relative',
          borderRadius: 16,
          padding: '28px 32px',
          marginBottom: 24,
          background: 'linear-gradient(135deg, #0f0c29 0%, #1a1040 40%, #0d1b3e 100%)',
          overflow: 'hidden',
          color: '#fff',
          boxShadow: '0 4px 32px rgba(99, 102, 241, 0.25), 0 1px 4px rgba(0, 0, 0, 0.15)',
        }}
      >
        {/* 背景光晕 */}
        <div
          style={{
            position: 'absolute',
            top: -40,
            right: -40,
            width: 220,
            height: 220,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, rgba(99, 102, 241, 0.1) 40%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: -60,
            left: '25%',
            width: 300,
            height: 150,
            borderRadius: '50%',
            background: 'radial-gradient(ellipse, rgba(59, 130, 246, 0.2) 0%, rgba(99, 102, 241, 0.08) 40%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />
        {/* 网格线装饰 */}
        <div
          className="tech-grid"
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
            pointerEvents: 'none',
          }}
        />

        <Row align="middle" gutter={[24, 16]} style={{ position: 'relative', zIndex: 1 }}>
          <Col>
            <Avatar
              size={72}
              icon={<UserOutlined />}
              className="tech-avatar-glow"
              style={{
                backgroundColor: 'transparent',
                border: '2px solid rgba(139, 92, 246, 0.6)',
                boxShadow: '0 0 28px rgba(139, 92, 246, 0.4), inset 0 0 20px rgba(139, 92, 246, 0.12)',
              }}
            />
          </Col>
          <Col flex="auto">
            <Title level={4} style={{ margin: 0, color: '#f8f7ff', fontWeight: 600, letterSpacing: 0.5 }}>
              欢迎回来，{profile?.name || '同学'}
            </Title>
            <Space size="middle" style={{ marginTop: 6 }}>
              <Text style={{ color: 'rgba(255,255,255,0.78)' }}>
                {profile?.level || '--'} 级 · 学习进度 {profile?.progress ?? 0}%
              </Text>
              {trendArrow && (
                <Text style={{ color: 'rgba(255,255,255,0.78)' }}>
                  {trendArrow} {evaluation?.recentTrend === 'up' ? '持续进步中' : '继续加油'}
                </Text>
              )}
            </Space>
            <br />
            <Space style={{ marginTop: 8 }}>
              {profile?.strengths?.map((s) => (
                <Tag
                  key={s}
                  color="purple"
                  style={{
                    borderRadius: 4,
                    background: 'rgba(139, 92, 246, 0.25)',
                    border: '1px solid rgba(139, 92, 246, 0.45)',
                    color: '#c4b5fd',
                    fontWeight: 500,
                  }}
                >
                  优势: {s}
                </Tag>
              ))}
              {profile?.weaknesses?.map((w) => (
                <Tag
                  key={w}
                  style={{
                    borderRadius: 4,
                    background: 'rgba(251, 191, 36, 0.18)',
                    border: '1px solid rgba(251, 191, 36, 0.4)',
                    color: '#fcd34d',
                    fontWeight: 500,
                  }}
                >
                  待提升: {w}
                </Tag>
              ))}
            </Space>
          </Col>
        </Row>
      </div>

      {/* ========== 统计卡片 — 玻璃拟态 ========== */}
      <Row gutter={[16, 16]}>
        {[
          {
            title: '综合评分',
            value: evaluation?.overallScore ?? 0,
            suffix: '分',
            icon: <TrophyOutlined />,
            color: '#aa3bff',
            trend: trendArrow,
          },
          {
            title: '学习进度',
            value: profile?.progress ?? 0,
            suffix: '%',
            icon: <RiseOutlined />,
            color: '#52c41a',
          },
          {
            title: '完成任务',
            value: evaluation?.completedTasks ?? 0,
            suffix: null,
            icon: <CheckCircleOutlined />,
            color: '#1677ff',
          },
          {
            title: '学习时长',
            value: evaluation?.totalHours ?? 0,
            suffix: 'h',
            icon: <ClockCircleOutlined />,
            color: '#fa8c16',
          },
        ].map((stat) => (
          <Col xs={24} sm={12} lg={6} key={stat.title}>
            <Card
              hoverable
              className="tech-stat-card"
              style={{
                borderRadius: 12,
                border: '1px solid var(--border, #e5e4e7)',
                background: 'rgba(255,255,255,0.82)',
                backdropFilter: 'blur(10px)',
                position: 'relative',
                overflow: 'hidden',
                boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)',
              }}
            >
              {/* 左侧彩色装饰条 */}
              <div
                style={{
                  position: 'absolute',
                  left: 0,
                  top: '15%',
                  height: '70%',
                  width: 3,
                  borderRadius: '0 3px 3px 0',
                  background: `linear-gradient(180deg, ${stat.color}, ${stat.color}cc)`,
                  opacity: 0.8,
                }}
              />
              <Statistic
                title={
                  <Text style={{ color: '#595959', fontSize: 13, fontWeight: 500 }}>{stat.title}</Text>
                }
                value={stat.value}
                suffix={
                  <span style={{ fontSize: 14 }}>
                    {stat.suffix} {stat.trend}
                  </span>
                }
                prefix={React.cloneElement(stat.icon, { style: { color: stat.color } })}
                valueStyle={{ color: '#1a1a2e', fontWeight: 700 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* ========== 六维画像雷达图 + 知识点 ========== */}
      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} md={14}>
          <Card
            className="tech-profile-card"
            style={{
              borderRadius: 12,
              border: '1px solid var(--border, #e5e4e7)',
              background: 'rgba(255,255,255,0.82)',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
            }}
          >
            <Title level={5} style={{ color: '#1a1a2e', marginBottom: 16 }}>
              <UserOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />
              六维学习画像
            </Title>
            <RadarChart dimensions={deriveDimensions(profile)} animated size={340} />
          </Card>
        </Col>

        <Col xs={24} md={10}>
          {/* 知识点掌握度 */}
          {profile?.topics?.length > 0 && (
            <Card
              style={{
                borderRadius: 12,
                border: '1px solid var(--border, #e5e4e7)',
                background: 'rgba(255,255,255,0.82)',
                backdropFilter: 'blur(10px)',
                boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                height: '100%',
              }}
            >
              <Title level={5} style={{ color: '#1a1a2e', marginBottom: 20 }}>
                <BookOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />
                知识点掌握度
              </Title>
              {profile.topics.map((topic) => {
                const pct = Math.round(topic.accuracy * 100)
                return (
                  <div key={topic.name} style={{ marginBottom: 20 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ color: '#1a1a2e', fontSize: 13, fontWeight: 500 }}>{topic.name}</Text>
                      <Text
                        className="tech-percent"
                        style={{ fontSize: 13, fontWeight: 600, color: pct >= 80 ? '#52c41a' : pct >= 60 ? '#fa8c16' : '#ff4d4f' }}
                      >
                        {pct}%
                      </Text>
                    </div>
                    <Progress
                      percent={pct}
                      size="small"
                      showInfo={false}
                      strokeColor={pct >= 80 ? { '0%': '#52c41a', '100%': '#73d13d' } : pct >= 60 ? { '0%': '#fa8c16', '100%': '#ffc53d' } : { '0%': '#ff4d4f', '100%': '#ff7a45' }}
                      trailColor="rgba(0,0,0,0.06)"
                    />
                  </div>
                )
              })}
            </Card>
          )}
        </Col>
      </Row>
    </div>
  )
}
