import { useState, useEffect } from 'react'
import { Typography, Button, Space, Card, Row, Col, Statistic, Tag, message } from 'antd'
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
import ProgressBar from '../components/ProgressBar'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { getLearningPath, generateLearningPath } from '../api/planner'
import { mockPath, mockStats } from '../mock/learningPathData'
import { shouldUseMock } from '../utils/useMock'

const USE_MOCK = shouldUseMock()

/**
 * SSE 事件类型：start | delta | data | error | done
 */
function parseSSEEvent(eventText) {
  try {
    return JSON.parse(eventText)
  } catch {
    return null
  }
}

const { Title, Text, Paragraph } = Typography

/**
 * 将后端 stages 转为 PathTimeline 期望的 nodes
 */
function stagesToNodes(stages, currentStage) {
  return stages.map((stage) => {
    const stageId = stage.stage_id
    let status = 'pending'
    if (stageId < currentStage) status = 'completed'
    else if (stageId === currentStage) status = 'in_progress'

    return {
      id: `stage-${stageId}`,
      title: stage.title,
      description: stage.description || stage.objectives?.join('；'),
      status,
      duration: `${stage.estimated_days || '?'}天`,
      difficulty: stage.difficulty,
      topics: stage.topics,
      tasks: stage.tasks,
    }
  })
}

/**
 * 学习路径页 — 时间线展示 + AI 生成
 */
export default function LearningPathPage() {
  const [pathData, setPathData] = useState(null)   // { student_id, title, stages, ... }
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    loadPath()
  }, [])

  async function loadPath() {
    setLoading(true)
    try {
      const data = await getLearningPath('demo-student-01')
      setPathData(data)
    } catch {
      // 后端不可用时使用 Mock 数据（仅在 VITE_USE_MOCK=true 时）
      if (USE_MOCK) {
        setTimeout(() => {
          setPathData(mockPath)
          setLoading(false)
        }, 600)
        return
      }
    }
  }

  /**
   * 生成新学习路径（SSE 流式）
   * SSE 事件：start → delta* → data → done
   */
  async function handleGenerate() {
    setGenerating(true)
    try {
      const response = await generateLearningPath({
        student_id: 'demo-student-01',
        goal: '掌握高中数学核心知识',
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''  // 保留未完成的行

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const eventData = line.slice(6)
            const event = parseSSEEvent(eventData)
            if (!event) continue

            switch (event.type) {
              case 'start':
                console.log('[Planner] 开始生成:', event.message)
                break

              case 'delta':
                // LLM 思考过程的增量文本，可按需展示
                break

              case 'data':
                // 结构化阶段数据到达
                setPathData({
                  student_id: 'demo-student-01',
                  title: event.title || '新学习路径',
                  stages: event.stages || [],
                })
                message.success('学习路径生成成功！')
                break

              case 'error':
                message.error(event.message || '生成失败')
                break

              case 'done':
                console.log('[Planner] 生成完成')
                break

              default:
                break
            }
          }
        }
      }
    } catch (err) {
      message.error('生成失败: ' + err.message)
      if (USE_MOCK) setPathData(mockPath)
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <LoadingSkeleton type="detail" />

  const stages = pathData?.stages || []
  const totalTasks = stages.reduce((sum, s) => sum + (s.tasks?.length || 0), 0)
  const completedTasks = stages.reduce(
    (sum, s) => sum + (s.tasks?.filter(t => t.status === 'completed')?.length || 0),
    0,
  )

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>学习路径</Title>
          {pathData?.goal && (
            <Text type="secondary">目标：{pathData.goal}</Text>
          )}
          {pathData?.total_estimated_days && (
            <Tag color="blue" style={{ marginLeft: 8 }}>
              预计 {pathData.total_estimated_days} 天
            </Tag>
          )}
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadPath}>刷新</Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleGenerate}
            loading={generating}
          >
            {generating ? '生成中...' : '生成新路径'}
          </Button>
        </Space>
      </div>

      {/* 统计卡片行 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        <Col xs={12} sm={6}>
          <Card className="stat-mini-card" size="small">
            <Statistic
              title="学习阶段"
              value={stages.length}
              prefix={<BookOutlined style={{ color: '#1677ff' }} />}
              suffix="个"
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="stat-mini-card" size="small">
            <Statistic
              title="已完成任务"
              value={completedTasks}
              suffix={<Text type="secondary">/ {totalTasks}</Text>}
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

      {/* 时间线 */}
      <Card className="path-main-card" bodyStyle={{ padding: 20 }}>
        {pathData ? (
          <PathTimeline
            title={pathData.title}
            stages={stages}
            overallProgress={pathData.overallProgress}
            onStageClick={(stage) => console.log('Stage:', stage.title)}
          />
        ) : (
          <Card>
            <div style={{ textAlign: 'center', padding: 48 }}>
              <BookOutlined style={{ fontSize: 40, color: '#d9d9d9' }} />
              <Paragraph type="secondary" style={{ marginTop: 16 }}>还没有学习路径</Paragraph>
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={handleGenerate}
                loading={generating}
              >
                AI 生成学习路径
              </Button>
            </div>
          </Card>
        )}
      </Card>
    </div>
  )
}
