import { useState, useCallback, useEffect } from 'react'
import {
  Typography, Button, Tabs, Space, List, Input, Modal,
  Drawer, Row, Col, Pagination, Empty, Select, message,
} from 'antd'
import {
  PlusOutlined, MessageOutlined, SearchOutlined,
  FilterOutlined, MenuOutlined,
  BookOutlined, AimOutlined,
} from '@ant-design/icons'
import ChatBox from '../components/ChatBox'
import ResourceCard from '../components/ResourceCard'
import PathTimeline from '../components/PathTimeline'
import MarkdownRenderer from '../components/MarkdownRenderer'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { useChat } from '../hooks/useChat'
import { askTutorStream, getTutorSessions, createTutorSession } from '../api/tutor'
import { getResources } from '../api/resource'
import { getLearningPath, generateLearningPath } from '../api/planner'
import { mockPath } from '../mock/learningPathData'
import { formatRelativeTime } from '../utils/format'

const { Title, Text } = Typography

const TYPE_OPTIONS = [
  { value: '', label: '全部类型' },
  { value: 'document', label: '文档' },
  { value: 'quiz', label: '练习题' },
  { value: 'mindmap', label: '思维导图' },
]

export default function TutorPage() {
  // ---- 会话 ----
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [newSessionModal, setNewSessionModal] = useState(false)
  const [newSessionTitle, setNewSessionTitle] = useState('')
  const [sessionsDrawer, setSessionsDrawer] = useState(false)

  // ---- 底部 Tab ----
  const [bottomTab, setBottomTab] = useState('resources')

  // ---- 学习资源 ----
  const [resources, setResources] = useState([])
  const [resLoading, setResLoading] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [resTotal, setResTotal] = useState(0)
  const [preview, setPreview] = useState(null)

  // ---- 学习路径 ----
  const [pathData, setPathData] = useState(null)
  const [pathLoading, setPathLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  const pageSize = 6

  const studentId = 'demo-student-01'

  // ---- 流式辅导对话 ----
  const streamFetcher = useCallback(
    (message, signal) =>
      askTutorStream({
        student_id: studentId,
        session_id: activeSessionId,
        message,
      }),
    [studentId, activeSessionId],
  )

  const { messages, isLoading, sendMessage, abort, setMessages } = useChat({
    streamFetcher,
    initialMessages: [
      {
        id: 'tutor-welcome',
        role: 'assistant',
        content:
          '你好！我是你的专属辅导老师。你可以问我任何学习上的问题：\n\n📖 **解题答疑** — 不会做的题目随时问我\n📝 **知识点讲解** — 帮你理解难懂的概念\n🎯 **练习推荐** — 根据你的薄弱点推荐题目\n💡 **学习建议** — 给你高效的学习方法指导\n\n告诉我你今天想学什么？',
      },
    ],
  })

  // ---- 初始化 ----
  useEffect(() => { loadSessions(); loadResources(); loadPath() }, [])

  // ---- 会话相关 ----
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

  async function handleNewSession() {
    if (!newSessionTitle.trim()) return
    try {
      const data = await createTutorSession({ student_id: studentId, title: newSessionTitle })
      setActiveSessionId(data?.id || data?.session_id)
      setNewSessionModal(false)
      setNewSessionTitle('')
      loadSessions()
      setMessages([{
        id: 'tutor-new', role: 'assistant',
        content: `新会话"${newSessionTitle}"已创建！请告诉我你想讨论什么问题？`,
      }])
    } catch { setNewSessionModal(false); setNewSessionTitle('') }
  }

  // ---- 资源相关 ----
  async function loadResources() {
    setResLoading(true)
    try {
      const params = { page, page_size: pageSize, keyword, type: type || undefined }
      const data = await getResources(params)
      setResources(Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [])
      setResTotal(data?.total || 0)
    } catch {
      const mockResources = [
        { id: '1', type: 'document', title: '二次函数知识点总结', description: '系统梳理二次函数的核心概念、图像特征与常见题型解题技巧', tags: ['数学', '函数', '初中'], createdAt: new Date() },
        { id: '2', type: 'quiz', title: '力学基础练习题', description: '涵盖牛顿三大定律、受力分析等基础概念的练习题目', tags: ['物理', '力学'], createdAt: new Date(Date.now() - 3600000) },
        { id: '3', type: 'mindmap', title: '英语语法体系', description: '以思维导图形式展示英语时态、语态、从句等语法框架', tags: ['英语', '语法'], createdAt: new Date(Date.now() - 7200000) },
        { id: '4', type: 'document', title: '电路分析方法', description: '讲解串并联电路、基尔霍夫定律等电路分析核心方法', tags: ['物理', '电学'], createdAt: new Date(Date.now() - 86400000) },
        { id: '5', type: 'quiz', title: '二次函数专项练习', description: '精选二次函数典型例题，涵盖图像判断、最值问题等题型', tags: ['数学', '函数'], createdAt: new Date(Date.now() - 172800000) },
        { id: '6', type: 'mindmap', title: '初中数学知识体系', description: '覆盖初中数学全部章节的知识结构思维导图', tags: ['数学', '综合'], createdAt: new Date(Date.now() - 259200000) },
      ]
      setResources(mockResources)
      setResTotal(6)
    } finally { setResLoading(false) }
  }

  function handleSearch() { setPage(1); loadResources() }

  // ---- 路径相关 ----
  async function loadPath() {
    setPathLoading(true)
    try {
      const data = await getLearningPath('demo-student-01')
      setPathData(data)
    } catch {
      setTimeout(() => { setPathData(mockPath); setPathLoading(false) }, 400)
      return
    }
    setPathLoading(false)
  }

  async function handleGeneratePath() {
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
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6))
              if (event.type === 'data') {
                setPathData({ student_id: 'demo-student-01', title: event.title || '新学习路径', stages: event.stages || [] })
                message.success('学习路径生成成功！')
              } else if (event.type === 'error') {
                message.error(event.message || '生成失败')
              }
            } catch { /* skip */ }
          }
        }
      }
    } catch {
      message.error('生成失败，已使用示例数据')
      setPathData(mockPath)
    } finally { setGenerating(false) }
  }

  // ---- 底部 Tab 内容 ----
  const stages = pathData?.stages || []

  const bottomTabs = [
    {
      key: 'resources',
      label: <span><BookOutlined /> 学习资源</span>,
      children: (
        <div style={{ height: '100%', overflowY: 'auto', padding: '12px 16px' }}>
          {/* 搜索筛选 */}
          <div style={{ marginBottom: 12 }}>
            <Space wrap>
              <Input
                placeholder="搜索资源..."
                prefix={<SearchOutlined />}
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onPressEnter={handleSearch}
                style={{ width: 200 }}
                size="small"
                allowClear
              />
              <Select
                value={type}
                onChange={setType}
                options={TYPE_OPTIONS}
                style={{ width: 120 }}
                size="small"
              />
              <Button type="primary" size="small" icon={<FilterOutlined />} onClick={handleSearch}>筛选</Button>
            </Space>
          </div>

          {resLoading ? (
            <LoadingSkeleton type="card" count={3} />
          ) : resources.length === 0 ? (
            <Empty description="没有找到符合条件的资源" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <>
              <Row gutter={[12, 12]}>
                {resources.map((r) => (
                  <Col xs={24} sm={12} md={8} key={r.id}>
                    <ResourceCard resource={r} onClick={setPreview} onDownload={(r) => console.log('Download:', r.id)} />
                  </Col>
                ))}
              </Row>
              {resTotal > pageSize && (
                <div style={{ textAlign: 'center', marginTop: 16 }}>
                  <Pagination current={page} pageSize={pageSize} total={resTotal} onChange={setPage} size="small" showSizeChanger={false} />
                </div>
              )}
            </>
          )}

          {/* 资源预览 */}
          {preview && (
            <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: 16, marginTop: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <Title level={5} style={{ margin: 0 }}>预览：{preview.title}</Title>
                <Button size="small" onClick={() => setPreview(null)}>关闭预览</Button>
              </div>
              <MarkdownRenderer content={`# ${preview.title}\n\n${preview.description}\n\n## 详细内容\n\n这里将显示资源完整内容...`} />
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'path',
      label: <span><AimOutlined /> 学习路径</span>,
      children: (
        <div style={{ height: '100%', overflowY: 'auto', padding: '12px 16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <Text strong style={{ fontSize: 15 }}>{pathData?.title || '我的学习路径'}</Text>
            <Button
              type="primary" size="small" icon={<PlusOutlined />}
              onClick={handleGeneratePath} loading={generating}
            >
              {generating ? '生成中...' : '生成新路径'}
            </Button>
          </div>

          {pathLoading ? (
            <LoadingSkeleton type="detail" />
          ) : pathData && stages.length > 0 ? (
            <PathTimeline
              title={pathData.title}
              stages={stages}
              overallProgress={pathData.overallProgress}
              onStageClick={(stage) => console.log('Stage:', stage.title)}
            />
          ) : (
            <Empty description="还没有学习路径，点击上方按钮生成" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </div>
      ),
    },
  ]

  // ==================== 渲染 ====================
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 56px - 48px)', overflow: 'hidden' }}>
      {/* ---- 顶部标题栏 ---- */}
      <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>🤖 智能辅导</Title>
          <Text type="secondary">随时提问，获取个性化学习指导</Text>
        </div>
        <Space>
          <Button icon={<MenuOutlined />} onClick={() => setSessionsDrawer(true)}>
            会话列表
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setNewSessionModal(true)}>
            新建会话
          </Button>
        </Space>
      </div>

      {/* ---- 中部：ChatBox（主体，自适应高度） ---- */}
      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', marginBottom: 12 }}>
        <div style={{
          flex: 1, minHeight: 300,
          border: '1px solid var(--border, #f0f0f0)',
          borderRadius: 12,
          overflow: 'hidden',
          display: 'flex', flexDirection: 'column',
          background: 'var(--bg-card, #fff)',
        }}>
          <ChatBox
            messages={messages}
            isLoading={isLoading}
            onSend={sendMessage}
            onAbort={abort}
            placeholder={activeSessionId ? '输入你的问题...' : '请先选择或创建会话'}
            showEmpty={false}
          />
        </div>
      </div>

      {/* ---- 底部：学习资源 / 学习路径 选择栏 ---- */}
      <div style={{
        flexShrink: 0,
        border: '1px solid var(--border, #f0f0f0)',
        borderRadius: 12,
        background: 'var(--bg-card, #fff)',
        overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
        maxHeight: '42%',
      }}>
        <Tabs
          className="tutor-bottom-tabs"
          activeKey={bottomTab}
          onChange={setBottomTab}
          items={bottomTabs}
          size="small"
          tabBarStyle={{ padding: '0 16px', marginBottom: 0, borderBottom: '1px solid #f0f0f0' }}
        />
      </div>

      {/* ---- 会话列表抽屉 ---- */}
      <Drawer
        title="辅导会话"
        open={sessionsDrawer}
        onClose={() => setSessionsDrawer(false)}
        placement="right"
        width={340}
      >
        {sessions.length === 0 ? (
          <Empty description="暂无会话" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <List
            loading={loadingSessions}
            dataSource={sessions}
            renderItem={(s) => (
              <List.Item
                style={{
                  cursor: 'pointer',
                  background: s.id === activeSessionId ? '#e6f4ff' : 'transparent',
                  padding: '10px 12px',
                  borderRadius: 8,
                  marginBottom: 4,
                }}
                onClick={() => { setActiveSessionId(s.id); setSessionsDrawer(false) }}
              >
                <List.Item.Meta
                  title={<Space><MessageOutlined /><Text>{s.title}</Text></Space>}
                  description={
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {s.messageCount || 0} 条 · {formatRelativeTime(s.updatedAt)}
                    </Text>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Drawer>

      {/* ---- 新建会话弹窗 ---- */}
      <Modal
        title="新建辅导会话"
        open={newSessionModal}
        onOk={handleNewSession}
        onCancel={() => setNewSessionModal(false)}
        okText="创建"
        cancelText="取消"
      >
        <Input
          placeholder="输入会话标题（如：二次函数答疑）"
          value={newSessionTitle}
          onChange={(e) => setNewSessionTitle(e.target.value)}
          onPressEnter={handleNewSession}
        />
      </Modal>
    </div>
  )
}
