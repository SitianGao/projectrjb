import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Typography, Space, List, Tag } from 'antd'
import {
  UserOutlined,
  BookOutlined,
  FileTextOutlined,
  TrophyOutlined,
  RiseOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { Link } from 'react-router-dom'
import { getProfile } from '../api/profile'
import { getStudentPaths } from '../api/planner'
import { getEvaluation } from '../api/evaluate'
import { formatRelativeTime, formatPercent } from '../utils/format'
import LoadingSkeleton from '../components/LoadingSkeleton'

const { Title, Text } = Typography

/**
 * 首页 / 仪表盘
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
            { id: '1', title: '高中数学 — 函数专题', status: 'in_progress', updatedAt: new Date() },
            { id: '2', title: '物理力学基础', status: 'completed', updatedAt: new Date(Date.now() - 86400000) },
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

  return (
    <div>
      <Title level={3}>仪表盘</Title>
      <Text type="secondary">欢迎回来，{profile?.name || '同学'}</Text>

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
              title="学习进度"
              value={profile?.progress || 0}
              suffix="%"
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a' }}
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
              value={evaluation?.totalHours || 0}
              suffix="h"
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 快捷入口 */}
      <Title level={4} style={{ marginTop: 32 }}>快捷入口</Title>
      <Row gutter={[16, 16]}>
        {quickLinks.map((link) => (
          <Col xs={24} sm={12} md={8} lg={4} key={link.to}>
            <Link to={link.to} style={{ textDecoration: 'none' }}>
              <Card hoverable style={{ textAlign: 'center', height: '100%' }}>
                <div style={{ fontSize: 32, color: '#1677ff', marginBottom: 8 }}>
                  {link.icon}
                </div>
                <Text strong>{link.label}</Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>{link.desc}</Text>
              </Card>
            </Link>
          </Col>
        ))}
      </Row>

      {/* 最近学习路径 */}
      <Title level={4} style={{ marginTop: 32 }}>学习路径</Title>
      {paths.length > 0 ? (
        <List
          dataSource={paths.slice(0, 5)}
          renderItem={(item) => (
            <List.Item
              extra={
                <Tag color={item.status === 'completed' ? 'success' : 'processing'}>
                  {item.status === 'completed' ? '已完成' : '进行中'}
                </Tag>
              }
            >
              <List.Item.Meta
                title={<Link to="/learning-path">{item.title}</Link>}
                description={`更新于 ${formatRelativeTime(item.updatedAt)}`}
              />
            </List.Item>
          )}
        />
      ) : (
        <Card>
          <Text type="secondary">暂无学习路径，前往 <Link to="/profile">画像页</Link> 开始创建</Text>
        </Card>
      )}
    </div>
  )
}
