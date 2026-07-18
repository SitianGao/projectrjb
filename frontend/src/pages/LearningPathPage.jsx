import { useState, useEffect } from 'react'
import { Typography, Button, Space, Card, Row, Col, Statistic, Tag, message, Modal, Progress, Alert, Result } from 'antd'
import {
  PlusOutlined,
  ReloadOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  BookOutlined,
  ThunderboltOutlined,
  FireOutlined,
  CheckCircleOutlined,
  RiseOutlined,
} from '@ant-design/icons'
import PathTimeline from '../components/PathTimeline'
import ProgressBar from '../components/ProgressBar'
import ForgettingCurve from '../components/ForgettingCurve'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { getLearningPath, generateLearningPath } from '../api/planner'
import { useAuth } from '../contexts/AuthContext'

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
  const { studentId } = useAuth()
  const [pathData, setPathData] = useState(null)   // { student_id, title, stages, ... }
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [detailType, setDetailType] = useState(null) // 'stages' | 'tasks' | 'time' | 'streak' | null

  useEffect(() => {
    loadPath()
  }, [studentId])

  async function loadPath() {
    setError(null)
    setLoading(true)
    try {
      const data = await getLearningPath(studentId)
      setPathData(data)
    } catch (err) {
      setError(err.message || '获取学习路径失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 生成新学习路径（SSE 流式）
   * SSE 事件：start → delta* → data → done
   */
  async function handleGenerate() {
    setGenerating(true)
    try {
      const response = await generateLearningPath({ student_id: studentId })

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
                  student_id: studentId,
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
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <LoadingSkeleton type="detail" />

  if (error) {
    return (
      <div style={{ maxWidth: 600, margin: '60px auto', padding: 24 }}>
        <Result
          status="error"
          title="加载失败"
          subTitle={error}
          extra={
            <Button type="primary" icon={<ReloadOutlined />} onClick={loadPath}>
              重新加载
            </Button>
          }
        />
      </div>
    )
  }

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
          <Card
            className="stat-mini-card"
            size="small"
            hoverable
            onClick={() => setDetailType('stages')}
            style={{ cursor: 'pointer' }}
          >
            <Statistic
              title="学习阶段"
              value={stages.length}
              prefix={<BookOutlined style={{ color: '#1677ff' }} />}
              suffix="个"
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card
            className="stat-mini-card"
            size="small"
            hoverable
            onClick={() => setDetailType('tasks')}
            style={{ cursor: 'pointer' }}
          >
            <Statistic
              title="已完成任务"
              value={completedTasks}
              suffix={<Text type="secondary">/ {totalTasks}</Text>}
              prefix={<TrophyOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card
            className="stat-mini-card"
            size="small"
            hoverable
            onClick={() => setDetailType('time')}
            style={{ cursor: 'pointer' }}
          >
            <Statistic
              title="学习时长"
              value="--"
              prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card
            className="stat-mini-card"
            size="small"
            hoverable
            onClick={() => setDetailType('streak')}
            style={{ cursor: 'pointer' }}
          >
            <Statistic
              title="连续学习"
              value="--"
              prefix={<FireOutlined style={{ color: '#eb2f96' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 艾宾浩斯遗忘曲线 */}
      <ForgettingCurve style={{ marginBottom: 20 }} />

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

      {/* ── 统计详情弹窗 ── */}
      {detailType && <DetailModalContent
        type={detailType}
        stages={stages}
        totalTasks={totalTasks}
        completedTasks={completedTasks}
        stats={null}
        onClose={() => setDetailType(null)}
      />}
    </div>
  )
}

// ──────────── 弹窗内容工厂（独立组件）────────────
const labelMap = ['日', '一', '二', '三', '四', '五', '六']
const TITLES = { stages: '学习阶段详情', tasks: '已完成任务详情', time: '学习时长详情', streak: '连续学习详情' }
const STATUS_LABEL = { completed: '已完成', in_progress: '进行中', pending: '待开始', locked: '未解锁' }
const STATUS_COLOR = { completed: '#52c41a', in_progress: '#1677ff', pending: '#fa8c16', locked: '#d9d9d9' }
const TASK_TYPE_LABEL = { study: '📖 学习', exercise: '✏️ 练习', quiz: '📝 测验', project: '🔨 项目' }

function DetailModalContent({ type, stages, totalTasks, completedTasks, stats, onClose }) {
  const allCompleted = stages.flatMap(s =>
    (s.tasks || []).filter(t => t.status === 'completed').map(t => ({ ...t, stageTitle: s.title, stageId: s.stage_id }))
  )

  // 本周学习日历
  const todayIdx = new Date().getDay()
  const mockWeek = labelMap.map((label, i) => {
    const offset = i - (todayIdx || 7) // 周一=0
    const d = new Date(); d.setDate(d.getDate() + offset)
    const studied = offset <= 0 && offset > -(stats?.streak || 0)
    return { label, date: `${d.getMonth() + 1}/${d.getDate()}`, studied }
  })

  let body
  switch (type) {
    case 'stages':
      body = stages.length === 0
        ? <Text type="secondary">暂无学习阶段数据</Text>
        : stages.map((s, i) => {
          const total = s.tasks?.length || 0
          const done = s.tasks?.filter(t => t.status === 'completed').length || 0
          return (
            <Card key={s.stage_id || i} size="small" style={{ marginBottom: 12, borderRadius: 8 }}
              title={
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Tag color={STATUS_COLOR[s.status]}>{STATUS_LABEL[s.status]}</Tag>
                  <Text strong>阶段 {s.stage_id || i + 1}：{s.title}</Text>
                </div>
              }
            >
              <Paragraph type="secondary" style={{ marginBottom: 8 }}>{s.description}</Paragraph>
              {s.objectives?.length > 0 && (
                <div style={{ marginBottom: 8 }}>
                  <Text strong>🎯 学习目标：</Text>
                  <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                    {s.objectives.map((obj, j) => <li key={j} style={{ fontSize: 13, color: '#666', lineHeight: 1.8 }}>{obj}</li>)}
                  </ul>
                </div>
              )}
              {s.topics?.length > 0 && (
                <div style={{ marginBottom: 8 }}>
                  <Text strong>🏷 知识点：</Text>
                  {s.topics.map(t => <Tag key={t} style={{ marginLeft: 4 }}>{t}</Tag>)}
                </div>
              )}
              <div style={{ display: 'flex', gap: 24, fontSize: 13, color: '#666' }}>
                <span>📋 任务：{done}/{total}</span>
                <span>📅 预计 {s.estimated_days || '?'} 天</span>
                <span>📊 难度：{s.difficulty || '未设定'}</span>
              </div>
              {total > 0 && <Progress percent={Math.round(done / total * 100)} size="small" style={{ marginTop: 8 }} strokeColor={done === total ? '#52c41a' : '#1677ff'} />}
            </Card>
          )
        })
      break

    case 'tasks':
      body = allCompleted.length === 0
        ? <div style={{ textAlign: 'center', padding: 24 }}><Text type="secondary">暂无已完成任务</Text></div>
        : <>
          <Paragraph type="secondary" style={{ marginBottom: 16 }}>
            共完成 <Text strong style={{ color: '#52c41a' }}>{allCompleted.length}</Text> 个任务
            （总任务 {totalTasks} 个，完成率 {totalTasks > 0 ? Math.round(completedTasks / totalTasks * 100) : 0}%）
          </Paragraph>
          {allCompleted.map(t => (
            <Card key={t.task_id} size="small" style={{ marginBottom: 10, borderRadius: 8, borderLeft: '3px solid #52c41a' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                <Text strong>{t.description}</Text>
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#666' }}>
                <Tag color="blue">来自：{t.stageTitle}</Tag>
                <span>{TASK_TYPE_LABEL[t.type] || t.type}</span>
                <span>难度：{t.difficulty}</span>
                <span>预计 {t.estimated_days} 天</span>
              </div>
            </Card>
          ))}
        </>
      break

    case 'time':
      body = <>
        <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
          <Col span={8}><Card size="small" style={{ textAlign: 'center', background: '#f6ffed' }}><Statistic title="总学习时长" value={stats?.totalStudyTime || '--'} prefix={<ClockCircleOutlined style={{ color: '#52c41a' }} />} /></Card></Col>
          <Col span={8}><Card size="small" style={{ textAlign: 'center', background: '#e6f4ff' }}><Statistic title="日均学习" value="--" prefix={<RiseOutlined style={{ color: '#1677ff' }} />} /></Card></Col>
          <Col span={8}><Card size="small" style={{ textAlign: 'center', background: '#fff7e6' }}><Statistic title="本周目标" value={`${stats?.weeklyGoal?.completed || 0}/${stats?.weeklyGoal?.total || 0}`} prefix={<TrophyOutlined style={{ color: '#fa8c16' }} />} suffix="项" /></Card></Col>
        </Row>
        <Text strong style={{ display: 'block', marginBottom: 12 }}>📊 各阶段学习时间分布</Text>
        {stages.length === 0 ? <Text type="secondary">暂无阶段数据</Text>
          : stages.map((s, i) => {
            const hours = (s.estimated_days || 1) * 2
            return (
              <div key={s.stage_id || i} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <Text style={{ fontSize: 13 }}>阶段 {s.stage_id || i + 1}：{s.title}</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>预计 {hours}h（{s.estimated_days || '?'}天 × {s.tasks?.length || 0}个任务）</Text>
                </div>
                <Progress percent={Math.min(100, hours / Math.max(...stages.map(st => (st.estimated_days || 1) * 2)) * 100)} strokeColor={`hsl(${(i * 60) % 360}, 70%, 50%)`} size="small" format={() => `${hours}h`} />
              </div>
            )
          })}
      </>
      break

    case 'streak':
      body = <>
        <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
          <Col span={12}><Card size="small" style={{ textAlign: 'center', background: '#fff0f6' }}><Statistic title="🔥 当前连续学习" value={stats?.streak || '--'} suffix="天" valueStyle={{ color: '#eb2f96', fontSize: 36 }} /></Card></Col>
          <Col span={12}><Card size="small" style={{ textAlign: 'center', background: '#f9f0ff' }}><Statistic title="🏆 最长连续记录" value={12} suffix="天" valueStyle={{ color: '#722ed1', fontSize: 36 }} /></Card></Col>
        </Row>
        <Text strong style={{ display: 'block', marginBottom: 12 }}>📅 本周学习日历</Text>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginBottom: 20 }}>
          {mockWeek.map((day, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>{day.label}</Text>
              <div style={{
                width: 40, height: 40, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: day.studied ? 'linear-gradient(135deg, #eb2f96, #f5222d)' : '#f5f5f5',
                color: day.studied ? '#fff' : '#ccc', fontWeight: day.studied ? 700 : 400, fontSize: 14,
              }}>{day.studied ? '✓' : day.date.split('/')[1]}</div>
              <Text type="secondary" style={{ fontSize: 11 }}>{day.date}</Text>
            </div>
          ))}
        </div>
        <Text strong style={{ display: 'block', marginBottom: 12 }}>💡 连续学习小贴士</Text>
        <Card size="small" style={{ background: '#fffbe6', borderRadius: 8, border: '1px solid #ffe58f' }}>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li style={{ marginBottom: 6 }}>每天坚持至少 <Text strong>30 分钟</Text>，保持学习节奏</li>
            <li style={{ marginBottom: 6 }}>连续 <Text strong>7 天</Text> 解锁"学习达人"徽章</li>
            <li style={{ marginBottom: 6 }}>连续 <Text strong>30 天</Text> 解锁"学霸"称号</li>
            <li>中断一天不会重置进度，但会降低连续计数</li>
          </ul>
        </Card>
      </>
      break

    default:
      body = null
  }

  return (
    <Modal
      title={TITLES[type] || '详情'}
      open
      onCancel={onClose}
      footer={null}
      width={720}
      style={{ top: 48 }}
      styles={{ body: { maxHeight: '78vh', overflow: 'auto', padding: '20px 28px' } }}
    >
      <div style={{ maxHeight: '70vh', overflow: 'auto' }}>
        {body}
      </div>
    </Modal>
  )
}
