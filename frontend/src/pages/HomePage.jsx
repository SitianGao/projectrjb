import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Typography, Space, List, Tag, Avatar, Progress } from 'antd'
import {
  UserOutlined,
  BookOutlined,
  FileTextOutlined,
  TrophyOutlined,
  RiseOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CaretUpOutlined,
  CaretDownOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { Link } from 'react-router-dom'
import { getProfile } from '../api/profile'
import { getStudentPaths } from '../api/planner'
import { getEvaluation } from '../api/evaluate'
import { formatRelativeTime, formatPercent } from '../utils/format'
import LoadingSkeleton from '../components/LoadingSkeleton'

const { Title, Text } = Typography

/**
 * 首页 / 个人中心
 *
 * 展示学生概况：画像摘要、学习进度、最近路径、快捷入口
 */
export default function HomePage() {
  const [profile, setProfile] = useState(null)
  const [paths, setPaths] = useState([])
  const [evaluation, setEvaluation] = useState(null)
  const [loading, setLoading] = useState(true)

  // 模拟学生 ID — 实际项目中从登录态获取
  const studentId = 'demo-student-01'

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      try {
        const [profileData, pathsData, evalData] = await Promise.all([
          getProfile(studentId).catch(() => null),
          getStudentPaths(studentId).catch(() => []),
          getEvaluation(studentId).catch(() => null),
        ])
        if (!cancelled) {
          setProfile(profileData)
          setPaths(Array.isArray(pathsData) ? pathsData : pathsData?.paths || [])
          setEvaluation(evalData)
        }
      } catch {
        // 后端不可用时使用模拟数据
        if (!cancelled) {
          setProfile({
            name: '张同学',
            level: '中级',
            progress: 65,
            strengths: ['数学', '物理'],
            weaknesses: ['英语'],
            topics: [
              { name: '二次函数', accuracy: 0.85 },
              { name: '力学', accuracy: 0.72 },
              { name: '电路', accuracy: 0.6 },
            ],
          })
          setPaths([
            { id: '1', title: '高中数学 — 函数专题', status: 'in_progress', progress: 62, updatedAt: new Date() },
            { id: '2', title: '物理力学基础', status: 'completed', progress: 100, updatedAt: new Date(Date.now() - 86400000) },
          ])
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
  }, [studentId])

  if (loading) return <LoadingSkeleton type="detail" />

  const quickLinks = [
    { to: '/profile', icon: <UserOutlined />, label: '学生画像', desc: '查看与完善个人信息' },
    { to: '/learning-path', icon: <RiseOutlined />, label: '学习路径', desc: '个性化学习规划' },
    { to: '/resources', icon: <FileTextOutlined />, label: '学习资源', desc: '文档、题目、思维导图' },
    { to: '/tutor', icon: <BookOutlined />, label: '智能辅导', desc: 'AI 一对一问答辅导' },
    { to: '/evaluate', icon: <TrophyOutlined />, label: '学习评估', desc: '进度追踪与评分' },
  ]

  /** 趋势箭头 */
  const trendArrow = evaluation?.recentTrend === 'up'
    ? <CaretUpOutlined style={{ color: '#52c41a', fontSize: 14 }} />
    : evaluation?.recentTrend === 'down'
      ? <CaretDownOutlined style={{ color: '#ff4d4f', fontSize: 14 }} />
      : null

  return (
    <div>
      {/* ========== 页面标题 ========== */}
      <Title level={3} style={{ color: '#1a1a2e', marginTop: -8, marginBottom: 12 }}>
        个人中心
      </Title>

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

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        {/* ========== 左列：快捷入口 + 知识点 ========== */}
        <Col xs={24} lg={12}>
          {/* 快捷入口 */}
          <div style={{ marginBottom: 24 }}>
            <Title level={5} style={{ color: '#1a1a2e', marginBottom: 16 }}>
              <ThunderboltOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />
              快捷入口
            </Title>
            <Row gutter={[12, 12]}>
              {quickLinks.map((link) => (
                <Col xs={12} sm={8} md={8} key={link.to}>
                  <Link to={link.to} style={{ textDecoration: 'none' }}>
                    <Card
                      hoverable
                      className="tech-quick-card"
                      style={{
                        borderRadius: 12,
                        textAlign: 'center',
                        height: '100%',
                        border: '1px solid var(--border, #e5e4e7)',
                        background: 'rgba(255,255,255,0.8)',
                        backdropFilter: 'blur(8px)',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                      }}
                    >
                      <div
                        className="tech-icon-circle"
                        style={{
                          width: 48,
                          height: 48,
                          borderRadius: 12,
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 22,
                          color: '#fff',
                          background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
                          marginBottom: 10,
                          boxShadow: '0 4px 14px rgba(139, 92, 246, 0.3)',
                          transition: 'transform 0.25s, box-shadow 0.25s',
                        }}
                      >
                        {link.icon}
                      </div>
                      <br />
                      <Text strong style={{ color: '#1a1a2e', fontSize: 13 }}>
                        {link.label}
                      </Text>
                      <br />
                      <Text style={{ fontSize: 11, color: '#8c8c8c' }}>
                        {link.desc}
                      </Text>
                    </Card>
                  </Link>
                </Col>
              ))}
            </Row>
          </div>

          {/* 知识点掌握度 */}
          {profile?.topics?.length > 0 && (
            <div>
              <Title level={5} style={{ color: '#1a1a2e', marginBottom: 16 }}>
                <BookOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />
                知识点掌握度
              </Title>
              <Card
                style={{
                  borderRadius: 12,
                  border: '1px solid var(--border, #e5e4e7)',
                  background: 'rgba(255,255,255,0.8)',
                  backdropFilter: 'blur(8px)',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                }}
              >
                {profile.topics.map((topic) => {
                  const pct = Math.round(topic.accuracy * 100)
                  return (
                    <div key={topic.name} style={{ marginBottom: 16 }}>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginBottom: 6,
                        }}
                      >
                        <Text style={{ color: '#1a1a2e', fontSize: 13, fontWeight: 500 }}>
                          {topic.name}
                        </Text>
                        <Text
                          className="tech-percent"
                          style={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: pct >= 80 ? '#52c41a' : pct >= 60 ? '#fa8c16' : '#ff4d4f',
                          }}
                        >
                          {pct}%
                        </Text>
                      </div>
                      <Progress
                        percent={pct}
                        size="small"
                        showInfo={false}
                        strokeColor={
                          pct >= 80
                            ? { '0%': '#52c41a', '100%': '#73d13d' }
                            : pct >= 60
                              ? { '0%': '#fa8c16', '100%': '#ffc53d' }
                              : { '0%': '#ff4d4f', '100%': '#ff7a45' }
                        }
                        trailColor="rgba(0,0,0,0.06)"
                      />
                    </div>
                  )
                })}
              </Card>
            </div>
          )}
        </Col>

        {/* ========== 右列：学习路径 ========== */}
        <Col xs={24} lg={12}>
          <Title level={5} style={{ color: '#1a1a2e', marginBottom: 16 }}>
            <RiseOutlined style={{ color: '#8b5cf6', marginRight: 8 }} />
            学习路径
          </Title>
          {paths.length > 0 ? (
            <Card
              style={{
                borderRadius: 12,
                border: '1px solid var(--border, #e5e4e7)',
                background: 'rgba(255,255,255,0.8)',
                backdropFilter: 'blur(8px)',
                boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
              }}
            >
              <List
                dataSource={paths.slice(0, 5)}
                renderItem={(item) => (
                  <List.Item
                    style={{
                      padding: '12px 0',
                      borderLeft: item.status === 'completed'
                        ? '3px solid #52c41a'
                        : '3px solid #8b5cf6',
                      paddingLeft: 14,
                      marginBottom: 4,
                      borderRadius: '0 6px 6px 0',
                      transition: 'background 0.2s',
                      background: 'transparent',
                    }}
                    className="tech-path-item"
                    extra={
                      <Space size="small">
                        {item.progress !== undefined && (
                          <Progress
                            percent={item.progress}
                            size="small"
                            style={{ width: 60 }}
                            showInfo={false}
                            strokeColor={
                              item.status === 'completed'
                                ? '#52c41a'
                                : { '0%': '#8b5cf6', '100%': '#6366f1' }
                            }
                            trailColor="rgba(0,0,0,0.06)"
                          />
                        )}
                        <Tag
                          color={item.status === 'completed' ? 'success' : 'processing'}
                          style={{ borderRadius: 4, fontSize: 11 }}
                        >
                          {item.status === 'completed' ? '已完成' : '进行中'}
                        </Tag>
                      </Space>
                    }
                  >
                    <List.Item.Meta
                      avatar={
                        <div
                          style={{
                            width: 32,
                            height: 32,
                            borderRadius: 8,
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background:
                              item.status === 'completed'
                                ? 'rgba(82,196,26,0.12)'
                                : 'rgba(139, 92, 246, 0.12)',
                          }}
                        >
                          <BookOutlined
                            style={{
                              color: item.status === 'completed' ? '#52c41a' : '#8b5cf6',
                              fontSize: 15,
                            }}
                          />
                        </div>
                      }
                      title={
                        <Link
                          to="/learning-path"
                          style={{ color: '#1a1a2e', fontWeight: 500, fontSize: 14 }}
                        >
                          {item.title}
                        </Link>
                      }
                      description={
                        <Text style={{ fontSize: 12, color: '#8c8c8c' }}>
                          更新于 {formatRelativeTime(item.updatedAt)}
                        </Text>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          ) : (
            <Card
              style={{
                borderRadius: 12,
                border: '1px solid var(--border, #e5e4e7)',
                textAlign: 'center',
                padding: '24px 0',
                background: 'rgba(255,255,255,0.8)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <BookOutlined
                style={{ fontSize: 48, color: 'rgba(139, 92, 246, 0.15)', marginBottom: 12 }}
              />
              <br />
              <Text type="secondary">
                暂无学习路径，前往 <Link to="/profile">画像页</Link> 开始创建
              </Text>
            </Card>
          )}
        </Col>
      </Row>
    </div>
  )
}
