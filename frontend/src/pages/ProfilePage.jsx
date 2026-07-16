import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Typography, Space, Row, Col, Card, Statistic, Input, Select, Button, Empty, Tag, message, Result, Spin } from 'antd'
import {
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  FilterOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  BookOutlined,
  ThunderboltOutlined,
  FireOutlined,
  MessageOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  RocketOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import ChatBox from '../components/ChatBox'
import ResourceCard from '../components/ResourceCard'
import MindMapViewer from '../components/MindMapViewer'
import MermaidChart from '../components/MermaidChart'
import MarkdownRenderer from '../components/MarkdownRenderer'
import PathTimeline from '../components/PathTimeline'
import ForgettingCurve from '../components/ForgettingCurve'
import LoadingSkeleton from '../components/LoadingSkeleton'
import MyCourses from '../components/MyCourses'
import { useChat, PHASE } from '../hooks/useChat'
import { startProfileChat, getProfile } from '../api/profile'
import { getResources } from '../api/resource'
import { getLearningPath, generateLearningPath } from '../api/planner'

import StageLineChart from '../components/StageLineChart'
import { getStageStatus } from '../utils/stageUtils'
const { Title, Text, Paragraph } = Typography

const SUGGESTIONS = [
  '帮我分析一下我的学习情况',
  '我的数学比较薄弱，怎么提升？',
  '推荐适合我的学习资源',
  '制定一个学习计划',
]

// 解释风格 → 提示词前缀
const STYLE_PROMPTS = {
  analogy: '请用生动的生活类比和比喻来解释以下问题，让我能通过熟悉的事物直观理解：',
  formula: '请用严谨的数学公式、推导步骤和逻辑论证来解释以下问题：',
  diagram: '请用文字描述流程图或使用 mermaid 语法画图的方式来解释以下问题，让结构一目了然：',
  story: '请用一个有趣的故事或真实案例来讲解以下知识点，让我在情境中自然理解：',
}

const TYPE_OPTIONS = [
  { value: '', label: '全部类型' },
  { value: 'document', label: '文档' },
  { value: 'quiz', label: '练习题' },
  { value: 'mindmap', label: '思维导图' },
]

function parseSSEEvent(t) { try { return JSON.parse(t) } catch { return null } }

// ==================== 学习资源面板 ====================
function ResourcePanel() {
  const [resources, setResources] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [keyword, setKeyword] = useState('')
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [preview, setPreview] = useState(null)

  useEffect(() => { loadResources() }, [page, type])

  async function loadResources() {
    setError(null)
    setLoading(true)
    try {
      const data = await getResources({ page, page_size: 12, keyword, type: type || undefined })
      setResources(Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [])
    } catch {
      setError('加载资源失败')
    } finally { setLoading(false) }
  }

  return (
    <div>
      <Space wrap style={{ marginBottom: 16 }}>
        <Input placeholder="搜索资源..." prefix={<SearchOutlined />} value={keyword}
          onChange={(e) => setKeyword(e.target.value)} onPressEnter={() => { setPage(1); loadResources() }}
          style={{ width: 200 }} allowClear />
        <Select value={type} onChange={setType} options={TYPE_OPTIONS} style={{ width: 120 }} />
        <Button type="primary" icon={<FilterOutlined />} onClick={() => { setPage(1); loadResources() }}>筛选</Button>
      </Space>
      {loading ? <LoadingSkeleton type="card" count={4} /> : error ? (
        <div style={{ textAlign: 'center', padding: 48 }}>
          <ExclamationCircleOutlined style={{ fontSize: 32, color: '#ff4d4f', marginBottom: 16 }} />
          <div style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 16 }}>{error}</div>
          <Button icon={<ReloadOutlined />} onClick={() => { setPage(1); loadResources() }}>重试</Button>
        </div>
      ) : resources.length === 0 ? (
        <Empty description="没有找到符合条件的资源" />
      ) : (
        <>
          <Row gutter={[12, 12]}>
            {resources.map((r) => (
              <Col xs={24} sm={12} md={8} lg={6} key={r.id}>
                <ResourceCard resource={r} onClick={setPreview} onDownload={(r) => console.log('Download:', r.id)} />
              </Col>
            ))}
          </Row>
          {preview && (
            <div style={{ marginTop: 24, borderTop: '1px solid var(--border)', paddingTop: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <Title level={5} style={{ margin: 0 }}>预览：{preview.title}</Title>
                <Button size="small" onClick={() => setPreview(null)}>关闭</Button>
              </div>
              {preview.type === 'mindmap' ? <MindMapViewer content={`# ${preview.title}\n## ${preview.description}`} />
                : preview.type === 'document' ? <MarkdownRenderer content={`# ${preview.title}\n\n${preview.description}`} />
                  : <MermaidChart chart={`graph TD\n  A["${String(preview.title).replace(/"/g, '\\"')}"] --> B["基础"]\n  A --> C["进阶"]`} />}
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ==================== 学习路径面板 ====================
function LearningPathPanel({ initialPathData = null }) {
  const [pathData, setPathData] = useState(initialPathData)
  const [loading, setLoading] = useState(!initialPathData)
  const [error, setError] = useState(null)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    if (!initialPathData) {
      loadPath()
    }
  }, [])

  async function loadPath() {
    setError(null)
    setLoading(true)
    try {
      const data = await getLearningPath('demo-student-01')
      setPathData(data)
    } catch {
      setError('加载学习路径失败')
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerate() {
    setGenerating(true)
    try {
      const resp = await generateLearningPath({ student_id: 'demo-student-01' })
      const reader = resp.body.getReader(); const dec = new TextDecoder(); let buf = ''
      while (true) {
        const { done, value } = await reader.read(); if (done) break
        buf += dec.decode(value, { stream: true })
        for (const line of buf.split('\n')) {
          buf = buf.includes('\n') ? buf.split('\n').pop() : ''
          if (line.startsWith('data: ')) {
            const evt = parseSSEEvent(line.slice(6))
            if (evt?.type === 'data') { setPathData({ student_id: 'demo-student-01', title: evt.title || '新路径', stages: evt.stages || [] }); message.success('生成成功！') }
            else if (evt?.type === 'error') message.error(evt.message)
          }
        }
      }
    } catch (err) { message.error('生成失败') }
    finally { setGenerating(false) }
  }

  if (loading) return <LoadingSkeleton type="detail" />

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <ExclamationCircleOutlined style={{ fontSize: 36, color: '#ff4d4f', marginBottom: 16 }} />
        <div style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 16 }}>{error}</div>
        <Space>
          <Button type="primary" icon={<ReloadOutlined />} onClick={loadPath}>重新加载</Button>
          <Button icon={<ThunderboltOutlined />} onClick={handleGenerate} loading={generating}>AI 生成</Button>
        </Space>
      </div>
    )
  }

  const stages = pathData?.stages || []
  const totalTasks = stages.reduce((s, st) => s + (st.tasks?.length || 0), 0)
  const completedTasks = stages.reduce((s, st) => s + (st.tasks?.filter(t => t.status === 'completed')?.length || 0), 0)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
        <Space>
          <Button size="small" icon={<ReloadOutlined />} onClick={loadPath}>刷新</Button>
          <Button size="small" type="primary" icon={<PlusOutlined />} onClick={handleGenerate} loading={generating}>
            {generating ? '生成中...' : '生成新路径'}
          </Button>
        </Space>
      </div>
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}><Card size="small"><Statistic title="学习阶段" value={stages.length} suffix="个" prefix={<BookOutlined style={{ color: '#1677ff' }} />} /></Card></Col>
        <Col xs={12} sm={6}><Card size="small"><Statistic title="已完成任务" value={completedTasks} suffix={<Text type="secondary">/ {totalTasks}</Text>} prefix={<TrophyOutlined style={{ color: '#52c41a' }} />} /></Card></Col>
        <Col xs={12} sm={6}><Card size="small"><Statistic title="学习时长" value="--" prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />} /></Card></Col>
        <Col xs={12} sm={6}><Card size="small"><Statistic title="连续学习" value="--" prefix={<FireOutlined style={{ color: '#eb2f96' }} />} /></Card></Col>
      </Row>
      <ForgettingCurve compact style={{ marginBottom: 16 }} />
      {pathData ? (
        <PathTimeline title={pathData.title} stages={stages} overallProgress={pathData.overallProgress}
          onStageClick={(s) => console.log('Stage:', s.title)} />
      ) : (
        <Card><div style={{ textAlign: 'center', padding: 32 }}>
          <BookOutlined style={{ fontSize: 32, color: 'var(--text-muted)' }} />
          <Paragraph type="secondary" style={{ marginTop: 12 }}>还没有学习路径</Paragraph>
          <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleGenerate} loading={generating}>AI 生成学习路径</Button>
        </div></Card>
      )}
    </div>
  )
}

// ==================== 主页面 ====================
export default function ProfilePage() {
  const navigate = useNavigate()
  const location = useLocation()

  // ── 状态恢复（页面刷新后从后端恢复）──
  const [stateRestored, setStateRestored] = useState(false)
  const [restoredPath, setRestoredPath] = useState(null)

  // ── 学习旅程生成状态 ──
  const [isStartingJourney, setIsStartingJourney] = useState(false)
  const [journeyError, setJourneyError] = useState(null)

  // 用于防止生成期间的重复点击
  const startingRef = useRef(false)

  // 页面加载时从后端恢复画像和学习路径状态
  useEffect(() => {
    let cancelled = false

    async function restoreState() {
      try {
        const [profileResult, pathResult] = await Promise.allSettled([
          getProfile('demo-student-01'),
          getLearningPath('demo-student-01'),
        ])

        if (cancelled) return

        const profile = profileResult.status === 'fulfilled' ? profileResult.value : null
        const path = pathResult.status === 'fulfilled' ? pathResult.value : null

        if (path && path.stages?.length > 0) {
          setRestoredPath(path)
        }
      } catch {
        // 恢复失败不影响使用，保持 collecting
      } finally {
        if (!cancelled) setStateRestored(true)
      }
    }

    restoreState()
    return () => { cancelled = true }
  }, [])

  const handleProfileUpdate = useCallback((updatedProfile) => {
    message.success('学习画像已更新 📊')
  }, [])

  // streamFetcher: 将 signal 传到 fetch，确保取消生效
  const streamFetcher = useCallback(
    (msg, signal, options) => {
      const style = options?.style
      const stylePrompt = STYLE_PROMPTS[style]
      const styledMsg = stylePrompt ? `${stylePrompt}\n\n${msg}` : msg
      return startProfileChat({
        student_id: 'demo-student-01',
        message: styledMsg,
        style,
        signal,
        history: options?.history,
        current_profile: options?.current_profile,
      })
    },
    [],
  )

  const {
    messages,
    isLoading,
    sendMessage,
    abort,
    completeness,
    nextQuestions,
    error: chatError,
    retryLastMessage,
    profile,
    phase,
    setPhase,
  } = useChat({
    streamFetcher,
    onProfileUpdate: handleProfileUpdate,
    initialMessages: [{
      id: 'welcome',
      role: 'assistant',
      content: '你好！我是你的专属学习助手 🤖\n\n让我们来聊聊你的学习情况吧：\n- 你的年级和目标？\n- 你擅长或不擅长的科目？\n- 你更喜欢的学习方式（看视频📺、读书📖、做题✏️）？\n\n告诉我这些，我会为你定制最佳学习路径！',
    }],
  })

  // 状态恢复后，根据后端数据同步阶段
  useEffect(() => {
    if (!stateRestored) return

    // 从 LandingPage"开始学习"按钮进入 → 始终显示 ChatBox
    if (location.state?.startChat) {
      return
    }

    if (restoredPath && restoredPath.stages?.length > 0) {
      // 已有学习路径 → 直接 active
      setPhase(PHASE.ACTIVE)
    }
    // 否则保持 useChat 内部根据 completeness 推导的阶段（collecting / ready）
  }, [stateRestored, restoredPath, setPhase, location.state?.startChat])

  // ── 开启学习之旅 ──
  // 严格按顺序调用:
  //   1. POST /api/planner/generate   (SSE: start/delta/data/error/done)
  //   2. 保存路径，获取 path_id
  //   3. 读取 current_stage → 选择第一个 topic
  //   4. POST /api/resource/generate  (传入 path_id)
  //   5. 轮询 GET /api/task/{task_id}/status → done
  //   6. 刷新路径 → 进入 active
  const handleStartJourney = useCallback(async () => {
    if (startingRef.current) return  // 防止重复点击
    startingRef.current = true
    setIsStartingJourney(true)
    setJourneyError(null)

    // 1. 进入 planning 阶段（兼容从 ready 或 failed 状态调用）
    setPhase(PHASE.PLANNING)

    try {
      // 2. 调用 POST /api/planner/generate
      //    只传 student_id；goal 必须来自最新画像（不硬编码）
      const goal = profile?.profile?.learning_goal || profile?.goal || undefined
      const response = await generateLearningPath({
        student_id: 'demo-student-01',
        ...(goal ? { goal } : {}),
      })

      if (!response || !response.body) {
        throw new Error('不支持流式响应')
      }

      // 3. 解析 SSE 事件: start / delta / data / error / done
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let pathData = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') continue

          try {
            const parsed = parseSSEEvent(data)
            if (!parsed) continue

            switch (parsed.type) {
              case 'start':
                // 流开始 — 元信息（可忽略）
                break
              case 'delta':
                // LLM 增量思考过程（可忽略）
                break
              case 'data': {
                // 4. 收到 data → 提取路径数据
                //    兼容两种格式: { stages } 直铺 或 { data: { stages } } 嵌套
                const pd = parsed.data || parsed
                if (pd && pd.stages?.length > 0) {
                  pathData = pd
                }
                break
              }
              case 'error':
                throw new Error(parsed.message || '路径生成失败')
              case 'done':
                break
            }
          } catch (parseErr) {
            // JSON 解析错误忽略，但业务错误继续抛出
            if (parseErr.message && !parseErr.message.includes('JSON')) {
              throw parseErr
            }
          }
        }
      }

      if (!pathData || !pathData.stages?.length) {
        throw new Error('未能生成学习路径，请重试')
      }

      // 路径已在后端自动持久化（planner_service 在 data 事件时 save_path）
      // 从后端获取完整路径数据（包含 path_id = id）
      let pathId = null
      try {
        const savedPath = await getLearningPath('demo-student-01')
        if (savedPath) {
          pathId = savedPath.id  // id 即为 path_id
          pathData = { ...pathData, ...savedPath }
          // 不在此处 setRestoredPath，避免触发 useEffect 竞态提前切到 ACTIVE
        }
      } catch {
        // 获取失败时尝试从 SSE data 中提取
        pathId = pathData.path_id || pathData.id || null
      }

      if (!pathId) {
        throw new Error('路径保存失败，缺少 path_id')
      }

      // 5. 读取 current_stage 对应阶段（1-indexed → 0-indexed）
      const currentStageIndex = (pathData.current_stage || 1) - 1
      const currentStage = pathData.stages[currentStageIndex]
      if (!currentStage) {
        throw new Error('路径缺少阶段信息')
      }

      // 6. 选择当前阶段第一个主要 topic
      const firstTopic = currentStage.topics?.[0] || currentStage.title
      if (!firstTopic) {
        throw new Error('当前阶段缺少学习主题')
      }

      // 跳转到资源生成进度页面
      navigate('/generating', {
        state: {
          studentId: 'demo-student-01',
          pathId,
          topic: firstTopic,
        },
      })
      setIsStartingJourney(false)
      startingRef.current = false

    } catch (err) {
      const errMsg = err.message || '学习路径生成失败，请重试'
      setJourneyError(errMsg)
      setPhase(PHASE.FAILED)
      message.error(errMsg)
      setIsStartingJourney(false)
      startingRef.current = false
    }
  }, [setPhase, profile, navigate])

  // 重试（从 failed 状态恢复 / 重新开始）
  const handleRetryJourney = useCallback(() => {
    setJourneyError(null)
    setRestoredPath(null) // 清除已保存的路径，防止 useEffect 立即切回 ACTIVE
    setPhase(PHASE.COLLECTING)
  }, [setPhase])

  // 点击阶段折线图拐点 → 跳转到阶段资源详情页
  const handleStageClick = useCallback(
    (stage, index) => {
      const path = restoredPath
      navigate(`/stage/${stage.stage_id}/resources`, {
        state: { stage, pathId: path?.id, pathData: path },
      })
    },
    [restoredPath, navigate],
  )

  const handleSuggestion = useCallback((t, opts) => sendMessage(t, opts), [sendMessage])
  const handleNextQuestion = useCallback((q) => sendMessage(q), [sendMessage])
  const handleDismissError = useCallback(() => {}, [])
  const handleRetry = useCallback(() => retryLastMessage?.(), [retryLastMessage])

  // ── 加载中：等待状态恢复 ──
  if (!stateRestored) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-page)' }}>
        <LoadingSkeleton type="detail" />
      </div>
    )
  }

  // ── 学习旅程已激活 → 折线图 + 阶段详情 ──
  if (phase === PHASE.ACTIVE) {
    const stages = restoredPath?.stages || []
    const currentStageNum = Number(restoredPath?.current_stage) || 1
    const currentStageData = stages.find((s) => Number(s.stage_id) === currentStageNum)
    const totalTasks = stages.reduce((s, st) => s + (st.tasks?.length || 0), 0)
    const completedTasks = stages.reduce(
      (s, st) => s + (st.tasks?.filter((t) => t.status === 'completed')?.length || 0),
      0,
    )

    return (
      <div style={{ height: '100%', overflow: 'auto', background: 'var(--bg-page)' }}>
        <div style={{ maxWidth: 1060, margin: '0 auto', padding: '24px' }}>
          {/* 页面标题 */}
          <div style={{ marginBottom: 20, textAlign: 'center' }}>
            <Title level={2} style={{ margin: 0, fontWeight: 700 }}>
              📐 我的课程
            </Title>
            {restoredPath?.goal && (
              <Text type="secondary" style={{ fontSize: 15 }}>
                学习目标：{restoredPath.goal}
              </Text>
            )}
            <div style={{ marginTop: 12 }}>
              <Button
                size="small"
                icon={<ReloadOutlined />}
                onClick={handleRetryJourney}
              >
                重新开始
              </Button>
            </div>
          </div>

          {/* 阶段折线图 */}
          <Card
            style={{ borderRadius: 16, marginBottom: 24 }}
            styles={{ body: { padding: '24px 16px 8px' } }}
          >
            <StageLineChart
              stages={stages}
              currentStage={currentStageNum}
              onStageClick={handleStageClick}
            />
            <div style={{ textAlign: 'center', marginTop: 4, marginBottom: 12 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                💡 点击拐点查看该阶段的学习资源
              </Text>
            </div>
          </Card>

          {/* 当前阶段详情卡片 */}
          {currentStageData && (
            <Card
              style={{
                borderRadius: 12,
                marginBottom: 24,
                border: '1px solid rgba(22,119,255,0.2)',
              }}
              styles={{ body: { padding: '20px 24px' } }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <div>
                  <Space size={8}>
                    <Text strong style={{ fontSize: 16 }}>
                      当前阶段：{currentStageData.title}
                    </Text>
                    <Tag color="blue">进行中</Tag>
                  </Space>
                  <Paragraph type="secondary" style={{ margin: '4px 0 0', fontSize: 13 }}>
                    {currentStageData.description}
                  </Paragraph>
                  <Space size={4} wrap style={{ marginTop: 4 }}>
                    {(currentStageData.topics || []).map((t) => (
                      <Tag key={t} color="purple" style={{ fontSize: 11 }}>
                        {t}
                      </Tag>
                    ))}
                  </Space>
                </div>
                <Button
                  type="primary"
                  onClick={() => handleStageClick(currentStageData, currentStageNum - 1)}
                >
                  查看当前阶段资源
                </Button>
              </div>
            </Card>
          )}

          {/* 统计卡片 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={12} sm={6}>
              <Card size="small" style={{ borderRadius: 10 }}>
                <Statistic
                  title="学习阶段"
                  value={stages.length}
                  suffix="个"
                  prefix={<BookOutlined style={{ color: '#1677ff' }} />}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card size="small" style={{ borderRadius: 10 }}>
                <Statistic
                  title="已完成任务"
                  value={completedTasks}
                  suffix={<Text type="secondary">/ {totalTasks}</Text>}
                  prefix={<TrophyOutlined style={{ color: '#52c41a' }} />}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card size="small" style={{ borderRadius: 10 }}>
                <Statistic
                  title="学习时长"
                  value="--"
                  prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card size="small" style={{ borderRadius: 10 }}>
                <Statistic
                  title="连续学习"
                  value="--"
                  prefix={<FireOutlined style={{ color: '#eb2f96' }} />}
                />
              </Card>
            </Col>
          </Row>

          {/* 学习路径面板（可折叠） */}
          <Card
            title={<Text strong style={{ fontSize: 16 }}>📐 学习路径详情</Text>}
            style={{ borderRadius: 12 }}
            styles={{ body: { padding: '12px 20px 20px' } }}
          >
            <LearningPathPanel initialPathData={restoredPath} />
          </Card>
        </div>

      </div>
    )
  }

  // ── failed 状态 ──
  if (phase === PHASE.FAILED) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-page)' }}>
        <Result
          status="error"
          title="学习路径生成失败"
          subTitle={journeyError || '生成过程中出现错误，请重试'}
          extra={
            <Space>
              <Button type="primary" icon={<ReloadOutlined />} onClick={handleRetryJourney}>
                重新开始
              </Button>
              <Button icon={<RocketOutlined />} onClick={handleStartJourney} loading={isStartingJourney}>
                再次尝试
              </Button>
            </Space>
          }
        />
      </div>
    )
  }

  // ── planning 阶段：显示生成进度 ──
  if (phase === PHASE.PLANNING) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-page)' }}>
        <div style={{
          maxWidth: 520, width: '100%', textAlign: 'center',
          padding: '48px 32px', borderRadius: 16,
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
        }}>
          <Spin size="large" />
          <Title level={4} style={{ marginTop: 24, marginBottom: 8 }}>
            🧠 正在生成学习路径...
          </Title>
          <Text type="secondary">
            AI 正在根据你的画像量身定制学习路径，请稍候
          </Text>
        </div>
      </div>
    )
  }

  // ── collecting / ready 阶段：显示画像采集 ChatBox ──
  return (
    <div style={{ height: '100%', overflow: 'auto', background: 'var(--bg-page)' }}>
      {/* 对话区 */}
        <div style={{
          display: 'flex', flexDirection: 'column',
          padding: '20px 24px 0',
          background: 'var(--bg-chat)',
        }}>
          {/* 项目标题 */}
          <div style={{ textAlign: 'center', marginBottom: 12 }}>
            <Title level={2} style={{ margin: 0, fontWeight: 700, background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', letterSpacing: 2 }}>
              智能学习平台
            </Title>
            <Text type="secondary" style={{ fontSize: 14 }}>个性化 AI 学习助手</Text>
          </div>

          {/* ChatBox 卡片 */}
          <div style={{
            height: 480,
            maxWidth: 800, margin: '0 auto', width: '100%',
            borderRadius: 16,
            overflow: 'hidden',
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            boxShadow: '0 2px 8px rgba(0,0,0,0.04), 0 12px 32px rgba(139,92,246,0.06)',
          }}>
            <ChatBox
              messages={messages}
              isLoading={isLoading}
              onSend={sendMessage}
              onAbort={abort}
              onRetry={handleRetry}
              placeholder="说说你的学习情况，我会为你定制学习方案..."
              emptyText="和 AI 助手聊聊你的学习情况"
              suggestions={SUGGESTIONS}
              onSuggestionClick={handleSuggestion}
              showStyleSelector={false}
              completeness={completeness}
              nextQuestions={nextQuestions}
              onNextQuestionClick={handleNextQuestion}
              chatError={chatError}
              onDismissError={handleDismissError}
              phase={phase}
              onStartJourney={handleStartJourney}
              isStartingJourney={isStartingJourney}
            />
          </div>

          {/* 我的课程栏目 */}
          <div style={{
            maxWidth: 1060,
            margin: '24px auto 0',
            width: '100%',
            padding: '0 24px 24px',
          }}>
            <MyCourses studentId="demo-student-01" />
          </div>

    </div>
    </div>
  )
}
