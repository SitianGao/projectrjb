import { useState, useEffect } from 'react'
import { Typography, Button, Space, Card, Row, Col, Statistic, Tabs, Tag } from 'antd'
const { Title, Text, Paragraph } = Typography
import {
  PlusOutlined,
  ReloadOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  BookOutlined,
  ThunderboltOutlined,
  FireOutlined,
} from '@ant-design/icons'
import PathTimeline from '../components/PathTimeline'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { getStudentPaths, generateLearningPathStream } from '../api/planner'
import { mockPaths, mockStats } from '../mock/learningPathData'

export default function LearningPathPage() {
  const [paths, setPaths] = useState([])
  const [loading, setLoading] = useState(true)
  const [activePathId, setActivePathId] = useState(null)

  useEffect(() => {
    loadPaths()
  }, [])

  async function loadPaths() {
    setLoading(true)
    try {
      const data = await getStudentPaths('demo-student-01')
      setPaths(Array.isArray(data) ? data : data?.paths || [])
    } catch {
      // 使用 Mock 数据
      setTimeout(() => {
        setPaths(mockPaths)
        setActivePathId(mockPaths[0]?.id)
        setLoading(false)
      }, 600)
      return
    }
    setLoading(false)
  }

  async function handleGenerate() {
    // 占位：后续接入真实生成流程
    console.log('Generate new path')
  }

  if (loading) return <LoadingSkeleton type="detail" />

  const activePath = paths.find(p => p.id === activePathId) || paths[0]
  const completedTotal = paths.reduce((sum, p) => sum + p.completedNodes, 0)
  const nodesTotal = paths.reduce((sum, p) => sum + p.totalNodes, 0)

  // Tab 项：每个路径一个 Tab
  const pathTabs = paths.map(p => ({
    key: p.id,
    label: (
      <Space size={4}>
        <span>{p.subject === '数学' ? '📐' : '📖'}</span>
        <span>{p.title}</span>
        <Tag style={{ fontSize: 10, lineHeight: '16px', marginLeft: 4 }}>
          {p.completedNodes}/{p.totalNodes}
        </Tag>
      </Space>
    ),
  }))

  return (
    <div className="learning-path-page">
      {/* 页面标题栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>📐 学习路径</Title>
          <Text type="secondary">AI 根据你的画像为你定制个性化学习路线</Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadPaths}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleGenerate}>
            生成新路径
          </Button>
        </Space>
      </div>

      {/* 统计卡片行 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        <Col xs={12} sm={6}>
          <Card className="stat-mini-card" size="small">
            <Statistic
              title="学习路径"
              value={paths.length}
              prefix={<BookOutlined style={{ color: '#1677ff' }} />}
              suffix="条"
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="stat-mini-card" size="small">
            <Statistic
              title="已完成节点"
              value={completedTotal}
              suffix={<Text type="secondary">/ {nodesTotal}</Text>}
              prefix={<TrophyOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="stat-mini-card" size="small">
            <Statistic
              title="学习时长"
              value={mockStats.totalStudyTime}
              prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="stat-mini-card" size="small">
            <Statistic
              title="连续学习"
              value={mockStats.streak}
              suffix="天"
              prefix={<FireOutlined style={{ color: '#eb2f96' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 路径选择 + 时间线 */}
      <Card className="path-main-card" bodyStyle={{ padding: 0 }}>
        {paths.length > 1 && (
          <div style={{ padding: '12px 20px 0' }}>
            <Tabs
              activeKey={activePathId}
              onChange={setActivePathId}
              items={pathTabs}
              size="small"
            />
          </div>
        )}

        <div style={{ padding: paths.length > 1 ? '0 20px 20px' : 20 }}>
          {activePath ? (
            <PathTimeline
              title={activePath.title}
              nodes={activePath.nodes}
              overallProgress={activePath.overallProgress}
              onNodeClick={(node) => console.log('Node:', node.title)}
            />
          ) : (
            <Card>
              <div style={{ textAlign: 'center', padding: 48 }}>
                <BookOutlined style={{ fontSize: 40, color: '#d9d9d9' }} />
                <Paragraph type="secondary" style={{ marginTop: 16 }}>还没有学习路径</Paragraph>
                <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleGenerate}>
                  AI 生成学习路径
                </Button>
              </div>
            </Card>
          )}
        </div>
      </Card>
    </div>
  )
}
