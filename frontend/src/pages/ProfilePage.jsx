import { useState, useEffect, useCallback } from 'react'
import { Typography, Space, Tabs, Row, Col, Card, Statistic, Input, Select, Button, Empty, Tag, List, Modal, message } from 'antd'
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
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  PushpinOutlined,
  PushpinFilled,
} from '@ant-design/icons'
import ChatBox from '../components/ChatBox'
import ProfileCard from '../components/ProfileCard'
import ResourceCard from '../components/ResourceCard'
import MindMapViewer from '../components/MindMapViewer'
import MermaidChart from '../components/MermaidChart'
import MarkdownRenderer from '../components/MarkdownRenderer'
import PathTimeline from '../components/PathTimeline'
import FloatingChat from '../components/FloatingChat'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { useChat } from '../hooks/useChat'
import { startProfileChat } from '../api/profile'
import { getResources } from '../api/resource'
import { getLearningPath, generateLearningPath } from '../api/planner'
import { getTutorSessions, createTutorSession } from '../api/tutor'
import ResourcePage from '../pages/ResourcePage'
import { mockPath, mockStats } from '../mock/learningPathData'
import { formatRelativeTime } from '../utils/format'

const { Title, Text, Paragraph } = Typography

const SUGGESTIONS = [
  '帮我分析一下我的学习情况',
  '我的数学比较薄弱，怎么提升？',
  '推荐适合我的学习资源',
  '制定一个学习计划',
]

const TYPE_OPTIONS = [
  { value: '', label: '全部类型' },
  { value: 'document', label: '文档' },
  { value: 'quiz', label: '练习题' },
  { value: 'mindmap', label: '思维导图' },
]

function parseSSEEvent(t) { try { return JSON.parse(t) } catch { return null } }

// ==================== 辅导面板 ====================
function TutorPanel({ collapsed, onToggle, locked, onLock }) {
  const [sessions, setSessions] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [newModal, setNewModal] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const studentId = 'demo-student-01'

  useEffect(() => { loadSessions() }, [])

  async function loadSessions() {
    setLoadingSessions(true)
    try {
      const data = await getTutorSessions(studentId)
      setSessions(Array.isArray(data) ? data : data?.sessions || [])
    } catch {
      setSessions([
        { id: 's1', title: '二次函数答疑', updatedAt: new Date(), messageCount: 12 },
        { id: 's2', title: '英语语法解惑', updatedAt: new Date(Date.now() - 86400000), messageCount: 8 },
      ])
    } finally { setLoadingSessions(false) }
  }

  async function handleNew() {
    if (!newTitle.trim()) return
    try {
      const data = await createTutorSession({ student_id: studentId, title: newTitle })
      setActiveId(data?.id || data?.session_id)
      setNewModal(false); setNewTitle('')
      loadSessions()
    } catch { setNewModal(false); setNewTitle('') }
  }

  return (
    <div style={{
      width: collapsed ? 44 : 260,
      flexShrink: 0,
      display: 'flex',
      borderRight: '1px solid rgba(255,255,255,0.06)',
      background: 'rgba(255,255,255,0.04)',
      transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      overflow: 'hidden',
      height: '100%',
    }}>
      {/* 收起态按钮 */}
      <div style={{
        width: 44, flexShrink: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 12,
        opacity: collapsed ? 1 : 0,
        transition: 'opacity 0.15s',
      }}>
        <Button type="text" icon={<MenuUnfoldOutlined />} onClick={onToggle} size="small" />
      </div>

      {/* 展开内容 */}
      <div style={{
        width: 216, flexShrink: 0,
        display: 'flex', flexDirection: 'column',
        opacity: collapsed ? 0 : 1,
        transition: 'opacity 0.15s',
      }}>
        <div style={{ padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <Space size={4}>
            <MessageOutlined style={{ color: '#8b5cf6' }} />
            <Text strong style={{ fontSize: 13 }}>辅导会话</Text>
          </Space>
          <Space size={4}>
            <Button type="text" size="small" icon={<PlusOutlined />} onClick={() => setNewModal(true)} />
            <Button type="text" size="small"
              icon={locked ? <PushpinFilled /> : <PushpinOutlined />}
              onClick={onLock}
              style={locked ? { color: '#8b5cf6' } : {}}
              title={locked ? '取消锁定' : '锁定面板'}
            />
            <Button type="text" size="small" icon={<MenuFoldOutlined />} onClick={onToggle} />
          </Space>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
          {loadingSessions ? <LoadingSkeleton type="card" count={2} /> : sessions.length === 0 ? (
            <Empty description="暂无会话" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ marginTop: 32 }} />
          ) : (
            <List size="small" dataSource={sessions} renderItem={(s) => (
              <List.Item onClick={() => setActiveId(s.id)}
                style={{
                  cursor: 'pointer', padding: '8px 12px',
                  background: s.id === activeId ? '#e6f4ff' : 'transparent',
                  borderBottom: '1px solid rgba(255,255,255,0.04)',
                }}>
                <List.Item.Meta
                  title={<Text style={{ fontSize: 13 }}>{s.title}</Text>}
                  description={<Text type="secondary" style={{ fontSize: 11 }}>{s.messageCount || 0} 条 · {formatRelativeTime(s.updatedAt)}</Text>}
                />
              </List.Item>
            )} />
          )}
        </div>

        <Modal title="新建辅导会话" open={newModal} onOk={handleNew} onCancel={() => setNewModal(false)} okText="创建" cancelText="取消">
          <Input placeholder="输入会话标题" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} onPressEnter={handleNew} />
        </Modal>
      </div>
    </div>
  )
}

// ==================== 学习资源面板 ====================
function ResourcePanel() {
  const [resources, setResources] = useState([])
  const [loading, setLoading] = useState(true)
  const [keyword, setKeyword] = useState('')
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [preview, setPreview] = useState(null)

  useEffect(() => { loadResources() }, [page, type])

  async function loadResources() {
    setLoading(true)
    try {
      const data = await getResources({ page, page_size: 12, keyword, type: type || undefined })
      setResources(Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [])
    } catch {
      setResources([
        { id: '1', type: 'document', title: '二次函数知识点总结', description: '核心概念与常见题型', tags: ['数学', '函数'], createdAt: new Date() },
        { id: '2', type: 'quiz', title: '力学基础练习题', description: '牛顿三大定律、受力分析', tags: ['物理', '力学'], createdAt: new Date() },
        { id: '3', type: 'mindmap', title: '英语语法体系', description: '时态、语态、从句框架', tags: ['英语', '语法'], createdAt: new Date() },
        { id: '4', type: 'document', title: '电路分析方法', description: '基尔霍夫定律核心方法', tags: ['物理', '电学'], createdAt: new Date() },
      ])
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
      {loading ? <LoadingSkeleton type="card" count={4} /> : resources.length === 0 ? (
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
            <div style={{ marginTop: 24, borderTop: '1px solid #f0f0f0', paddingTop: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <Title level={5} style={{ margin: 0 }}>预览：{preview.title}</Title>
                <Button size="small" onClick={() => setPreview(null)}>关闭</Button>
              </div>
              {preview.type === 'mindmap' ? <MindMapViewer content={`# ${preview.title}\n## ${preview.description}`} />
                : preview.type === 'document' ? <MarkdownRenderer content={`# ${preview.title}\n\n${preview.description}`} />
                  : <MermaidChart chart={`graph TD\n  A[${preview.title}] --> B[基础]\n  A --> C[进阶]`} />}
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ==================== 学习路径面板 ====================
function LearningPathPanel() {
  const [pathData, setPathData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => { loadPath() }, [])

  async function loadPath() {
    setLoading(true)
    try { const data = await getLearningPath('demo-student-01'); setPathData(data) }
    catch { setTimeout(() => { setPathData(mockPath); setLoading(false) }, 600); return }
    setLoading(false)
  }

  async function handleGenerate() {
    setGenerating(true)
    try {
      const resp = await generateLearningPath({ student_id: 'demo-student-01', goal: '掌握高中数学核心知识' })
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
    } catch (err) { message.error('生成失败'); setPathData(mockPath) }
    finally { setGenerating(false) }
  }

  if (loading) return <LoadingSkeleton type="detail" />
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
        <Col xs={12} sm={6}><Card size="small"><Statistic title="学习时长" value={mockStats.totalStudyTime} prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />} /></Card></Col>
        <Col xs={12} sm={6}><Card size="small"><Statistic title="连续学习" value={mockStats.streak} suffix="天" prefix={<FireOutlined style={{ color: '#eb2f96' }} />} /></Card></Col>
      </Row>
      {pathData ? (
        <PathTimeline title={pathData.title} stages={stages} overallProgress={pathData.overallProgress}
          onStageClick={(s) => console.log('Stage:', s.title)} />
      ) : (
        <Card><div style={{ textAlign: 'center', padding: 32 }}>
          <BookOutlined style={{ fontSize: 32, color: '#d9d9d9' }} />
          <Paragraph type="secondary" style={{ marginTop: 12 }}>还没有学习路径</Paragraph>
          <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleGenerate} loading={generating}>AI 生成学习路径</Button>
        </div></Card>
      )}
    </div>
  )
}

// ==================== 主页面 ====================
export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState('resource')
  const [tutorHover, setTutorHover] = useState(false)
  const [tutorLocked, setTutorLocked] = useState(false)
  const [profile, setProfile] = useState(null)

  const handleProfileUpdate = useCallback((updatedProfile) => {
    setProfile(updatedProfile)
    message.success('学习画像已更新 📊')
  }, [])

  const streamFetcher = useCallback(
    (msg, signal) => startProfileChat({ student_id: 'demo-student-01', message: msg }),
    [],
  )
  const { messages, isLoading, sendMessage, abort } = useChat({
    streamFetcher,
    onProfileUpdate: handleProfileUpdate,
    initialMessages: [{
      id: 'welcome',
      role: 'assistant',
      content: '你好！我是你的专属学习助手 🤖\n\n让我们来聊聊你的学习情况吧：\n- 你的年级和目标？\n- 你擅长或不擅长的科目？\n- 你更喜欢的学习方式（看视频📺、读书📖、做题✏️）？\n\n告诉我这些，我会为你定制最佳学习路径！',
    }],
  })
  const handleSuggestion = useCallback((t) => sendMessage(t), [sendMessage])

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden', background: 'var(--bg-page)' }}>
      {/* ===== 左侧：辅导面板 ===== */}
      <div
        onMouseEnter={() => { if (!tutorLocked) setTutorHover(true) }}
        onMouseLeave={() => { if (!tutorLocked) setTutorHover(false) }}
        style={{ flexShrink: 0 }}
      >
        <TutorPanel
          collapsed={!tutorHover && !tutorLocked}
          locked={tutorLocked}
          onToggle={() => setTutorHover(!tutorHover)}
          onLock={() => { setTutorLocked(!tutorLocked); if (!tutorLocked) setTutorHover(true) }}
        />
      </div>

      {/* ===== 右侧：主内容区 ===== */}
      <div style={{ flex: 1, minWidth: 0, overflow: 'auto' }}>
        {/* 对话区 */}
        <div style={{
          display: 'flex', flexDirection: 'column',
          padding: '64px 24px 0',
          background: 'var(--bg-chat)',
        }}>
          {/* 项目标题 */}
          <div style={{ textAlign: 'center', marginBottom: 20 }}>
            <Title level={2} style={{ margin: 0, fontWeight: 700, background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', letterSpacing: 2 }}>
              🤖 智能学习平台
            </Title>
            <Text type="secondary" style={{ fontSize: 14 }}>个性化 AI 学习助手</Text>
          </div>

          {/* ChatBox 卡片 + 画像卡片 */}
          <div style={{ display: 'flex', gap: 16, maxWidth: 1100, margin: '0 auto', width: '100%' }}>
            <div style={{
              flex: 1, minWidth: 0,
              height: 350,
              borderRadius: 16,
              overflow: 'hidden',
              background: 'var(--bg-card)',
              border: '1px solid #e8e8ed',
              boxShadow: '0 2px 8px rgba(0,0,0,0.04), 0 12px 32px rgba(139,92,246,0.06)',
            }}>
              <ChatBox
                messages={messages}
                isLoading={isLoading}
                onSend={sendMessage}
                onAbort={abort}
                placeholder="说说你的学习情况，我会为你定制学习方案..."
                emptyText="和 AI 助手聊聊你的学习情况"
                suggestions={SUGGESTIONS}
                onSuggestionClick={handleSuggestion}
              />
            </div>
            <div style={{
              width: 320, flexShrink: 0, height: 350, overflow: 'auto',
              borderRadius: 16,
              background: 'var(--bg-card)',
              border: '1px solid #e8e8ed',
              boxShadow: '0 2px 8px rgba(0,0,0,0.04), 0 12px 32px rgba(139,92,246,0.06)',
            }}>
              {profile ? (
                <ProfileCard profile={profile} compact />
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Empty description="发送消息，AI 将构建你的学习画像" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Tab 区 */}
        <div style={{ padding: '0 24px 24px' }}>
          <div style={{
            maxWidth: 800, margin: '0 auto', width: '100%',
            padding: '8px 0 20px',
          }}>
            <Tabs activeKey={activeTab} onChange={setActiveTab} centered
              items={[
                { key: 'resource', label: '📄 学习资源', children: null },
                { key: 'path', label: '📐 学习路径', children: null },
              ]} />
            <div style={{ maxWidth: 960, margin: '0 auto', width: '100%' }}>
              {activeTab === 'resource' ? <ResourcePage /> : <LearningPathPanel />}
            </div>
          </div>
        </div>
      </div>

      {/* 右下角悬浮对话 */}
      <FloatingChat />
    </div>
  )
}
