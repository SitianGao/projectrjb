import { useState, useCallback, useEffect, useMemo } from 'react'
import {
  Typography, Button, Space, List, Input, Modal,
  Drawer, Row, Col, Pagination, Empty, Select, message,
  Segmented, Collapse,
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
import KnowledgePanel from '../components/KnowledgePanel'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { useChat } from '../hooks/useChat'
import { askTutorStream, getTutorSessions, createTutorSession } from '../api/tutor'
import { getResources } from '../api/resource'
import { getLearningPath, generateLearningPath } from '../api/planner'
import { mockPath } from '../mock/learningPathData'
import { formatRelativeTime } from '../utils/format'
import { shouldUseMock } from '../utils/useMock'

const USE_MOCK = shouldUseMock()

const { Title, Text } = Typography

const TYPE_OPTIONS = [
  { value: '', label: '全部类型' },
  { value: 'document', label: '文档' },
  { value: 'quiz', label: '练习题' },
  { value: 'mindmap', label: '思维导图' },
]

const EXPLANATION_STYLES = [
  { value: 'analogy', label: '🔗 类比' },
  { value: 'formula', label: '📐 公式' },
  { value: 'visual', label: '📊 图解' },
  { value: 'story', label: '📖 故事' },
]

// ==================== Mock 流式回复内容 ====================
function getMockAnswer(style, message) {
  const topic = message.length > 20 ? message.slice(0, 20) + '...' : message

  const answers = {
    analogy: `## 💡 用类比来理解"${topic}"\n\n想象一下，这就像**煮饺子** 🥟——\n\n- **准备工作**好比理解基本概念，面粉和馅料要分开准备\n- **包饺子**就像把知识点串联起来，每个褶子都是一次练习\n- **下锅煮**就是应用实践，火候（难度）要恰到好处\n\n> 💭 **记住**：饺子浮起来就是熟了——当你能够独立解决问题时，就说明你真的掌握了！\n\n### 生活类比\n\n| 概念 | 类比 |\n|:---|:---|\n| 基础理论 | 食材准备 |\n| 公式推导 | 包饺子手法 |\n| 实战练习 | 煮饺子的火候 |\n`,

    formula: `## 📐 公式推导："${topic}"\n\n### 1. 基本定义\n\n设函数 $f(x)$ 在区间 $[a, b]$ 上连续，在 $(a, b)$ 内可导。\n\n### 2. 核心公式\n\n$$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$\n\n### 3. 推导步骤\n\n**步骤 1**：建立差商\n\n$$\\frac{\\Delta y}{\\Delta x} = \\frac{f(x_0 + \\Delta x) - f(x_0)}{\\Delta x}$$\n\n**步骤 2**：取极限\n\n$$f'(x_0) = \\lim_{\\Delta x \\to 0} \\frac{f(x_0 + \\Delta x) - f(x_0)}{\\Delta x}$$\n\n**步骤 3**：应用\n\n| 函数 | 导数 |\n|:---|:---|\n| $x^n$ | $nx^{n-1}$ |\n| $\\sin x$ | $\\cos x$ |\n| $e^x$ | $e^x$ |\n\n> 📌 **关键点**：导数的本质是变化率，几何意义是切线斜率。\n`,

    visual: `## 📊 图解："${topic}"\n\n让我们用流程图来可视化核心逻辑：\n\n\`\`\`mermaid\ngraph TD\n    A["理解基本概念"] --> B["掌握核心公式"]\n    B --> C["做典型例题"]\n    C --> D["总结解题模板"]\n    D --> E["攻克综合难题"]\n    E --> F["形成知识体系"]\n    \n    style A fill:#e6f7ff,stroke:#1890ff\n    style F fill:#f6ffed,stroke:#52c41a\n\`\`\`\n\n### 知识结构\n\n\`\`\`mermaid\ngraph LR\n    subgraph 基础层\n    A[定义] --> B[性质]\n    end\n    subgraph 应用层\n    B --> C[定理]\n    C --> D[公式]\n    end\n    subgraph 进阶层\n    D --> E[解题技巧]\n    E --> F[综合应用]\n    end\n\`\`\`\n\n> 🎯 从上图可以看出，知识点是层层递进的，先打好基础再逐步深入。\n`,

    story: `## 📖 小明的学习故事\n\n小明最近在学习 **"${topic}"**，一开始他觉得很困惑 🤔\n\n### 第一章：迷茫\n\n> "这个概念好抽象啊！"小明看着课本发愁。\n\n他尝试了做题，但总是出错。错题本上已经记了十几道了...\n\n### 第二章：转机\n\n有一天，老师用一个生活中的例子讲解了这个概念。\n\n> 💡 **顿悟时刻**："原来如此！这不就是......"\n\n小明突然发现，只要换个角度思考，一切都变得清晰了。\n\n### 第三章：突破\n\n掌握了窍门之后，小明开始系统地练习：\n\n1. **第 1-3 天**：每天 5 道基础题，巩固概念\n2. **第 4-7 天**：每天 3 道进阶题，举一反三\n3. **第 8-14 天**：每周 2 套综合卷，查漏补缺\n\n### 第四章：收获 🎉\n\n两周后，小明在测验中取得了 **92 分**！\n\n> 🌟 **他的心得**："学习最重要的不是死记硬背，而是找到适合自己的理解方式。"\n\n---\n\n这个故事告诉我们：**困难只是暂时的，方法对了，一切都会好起来！**\n`,
  }

  return answers[style] || answers.analogy
}

// ==================== Mock 知识面板数据 ====================
function getMockKnowledgeData(style) {
  const dataMap = {
    analogy: {
      diagrams: [],
      references: [
        { title: '生活类比学习法', description: '将抽象概念映射到日常经验中' },
        { title: '认知心理学基础', description: '类比推理是人类最自然的学习方式之一' },
        { title: '常见类比模式', description: '结构映射、关系类比、特征类比' },
      ],
    },
    formula: {
      diagrams: [
        { title: '公式推导链路', chart: 'graph TD\n  A[定义] --> B[引理]\n  B --> C[定理]\n  C --> D[公式]\n  D --> E[应用]' },
      ],
      references: [
        { title: '数学推导方法论', description: '从公理出发，逐步推导' },
        { title: '常用公式速查', description: '整理核心公式及其适用条件' },
      ],
    },
    visual: {
      diagrams: [
        { title: '思维导图', chart: 'graph TD\n  A[核心概念] --> B[子概念1]\n  A --> C[子概念2]\n  B --> D[应用1]\n  C --> E[应用2]\n  D --> F[综合]\n  E --> F' },
        { title: '学习路径', chart: 'graph LR\n  A[入门] --> B[基础]\n  B --> C[进阶]\n  C --> D[精通]\n\n  style A fill:#e6f7ff\n  style D fill:#f6ffed' },
      ],
      references: [
        { title: '思维导图制作指南', description: '如何将知识结构可视化' },
        { title: '流程图设计原则', description: '清晰、简洁、层次分明' },
      ],
    },
    story: {
      diagrams: [],
      references: [
        { title: '叙事学习理论', description: '通过故事构建知识的情境记忆' },
        { title: '教育心理学', description: '故事情境如何促进长期记忆' },
        { title: '案例教学法', description: '用真实案例串联知识点' },
      ],
    },
  }
  return dataMap[style] || dataMap.analogy
}

/**
 * 从 Markdown 内容中提取 Mermaid 代码块
 */
function extractDiagrams(markdownContent) {
  const mermaidRegex = /```mermaid\n([\s\S]*?)```/g
  const diagrams = []
  let match
  let idx = 0
  while ((match = mermaidRegex.exec(markdownContent)) !== null) {
    diagrams.push({ title: `流程图 ${++idx}`, chart: match[1].trim() })
  }
  return diagrams
}

// ==================== 主组件 ====================
export default function TutorPage() {
  // ---- 解释风格 ----
  const [explanationStyle, setExplanationStyle] = useState('analogy')

  // ---- 知识面板 ----
  const [knowledgeDiagrams, setKnowledgeDiagrams] = useState([])
  const [knowledgeReferences, setKnowledgeReferences] = useState([])

  // ---- 会话 ----
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [newSessionModal, setNewSessionModal] = useState(false)
  const [newSessionTitle, setNewSessionTitle] = useState('')
  const [sessionsDrawer, setSessionsDrawer] = useState(false)

  // ---- 资源面板（右侧折叠） ----
  const [resources, setResources] = useState([])
  const [resLoading, setResLoading] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [resTotal, setResTotal] = useState(0)
  const [preview, setPreview] = useState(null)
  const pageSize = 6

  // ---- 学习路径面板（右侧折叠） ----
  const [pathData, setPathData] = useState(null)
  const [pathLoading, setPathLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  const studentId = 'demo-student-01'

  // ---- 处理 SSE 结构化事件 ----
  const handleSSEEvent = useCallback((event) => {
    // 捕获 diagrams
    if (event.diagrams && Array.isArray(event.diagrams)) {
      setKnowledgeDiagrams((prev) => [...prev, ...event.diagrams])
    }
    // 捕获 references
    if (event.references && Array.isArray(event.references)) {
      setKnowledgeReferences((prev) => [...prev, ...event.references])
    }
    // 处理 data 事件中的结构化字段
    if (event.type === 'data') {
      if (event.diagrams) {
        setKnowledgeDiagrams((prev) => [...prev, ...(Array.isArray(event.diagrams) ? event.diagrams : [event.diagrams])])
      }
      if (event.references) {
        setKnowledgeReferences((prev) => [...prev, ...(Array.isArray(event.references) ? event.references : [event.references])])
      }
    }
  }, [])

  // ---- 流式辅导对话 ----
  const realStreamFetcher = useCallback(
    (message, signal) =>
      askTutorStream({
        student_id: studentId,
        session_id: activeSessionId,
        message,
        explanation_style: explanationStyle,
      }),
    [studentId, activeSessionId, explanationStyle],
  )

  // ---- Mock 流式 fetcher ----
  const mockStreamFetcher = useCallback(
    async (message, signal) => {
      const content = getMockAnswer(explanationStyle, message)
      const knowledgeData = getMockKnowledgeData(explanationStyle)
      const encoder = new TextEncoder()

      const stream = new ReadableStream({
        async start(controller) {
          try {
            // 发送 start 事件
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'start', message: '开始生成' })}\n\n`))
            await new Promise((r) => setTimeout(r, 200))

            // 逐字发送内容
            for (let i = 0; i < content.length; i++) {
              if (signal?.aborted) return
              // 每 3-8 个字符发送一次，模拟流式
              const chunkSize = 3 + Math.floor(Math.random() * 6)
              const chunk = content.slice(i, i + chunkSize)
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content: chunk })}\n\n`))
              i += chunkSize - 1
              await new Promise((r) => setTimeout(r, 20 + Math.random() * 25))
            }

            // 发送结构化数据事件
            if (knowledgeData.diagrams.length > 0 || knowledgeData.references.length > 0) {
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({
                type: 'data',
                diagrams: knowledgeData.diagrams,
                references: knowledgeData.references,
              })}\n\n`))
              await new Promise((r) => setTimeout(r, 100))
            }

            // 发送完成事件
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'done' })}\n\n`))
            controller.close()
          } catch {
            controller.close()
          }
        },
      })

      return new Response(stream, {
        headers: { 'Content-Type': 'text/event-stream' },
      })
    },
    [explanationStyle],
  )

  const streamFetcher = USE_MOCK ? mockStreamFetcher : realStreamFetcher

  const {
    messages, isLoading, sendMessage, abort, setMessages,
  } = useChat({
    streamFetcher,
    onSSEEvent: handleSSEEvent,
    initialMessages: [
      {
        id: 'tutor-welcome',
        role: 'assistant',
        content:
          '你好！我是你的专属辅导老师。你可以问我任何学习上的问题：\n\n📖 **解题答疑** — 不会做的题目随时问我\n📝 **知识点讲解** — 帮你理解难懂的概念\n🎯 **练习推荐** — 根据你的薄弱点推荐题目\n💡 **学习建议** — 给你高效的学习方法指导\n\n> 💡 试试切换右上方的**解释风格**来体验不同的讲解方式！\n\n告诉我你今天想学什么？',
      },
    ],
  })

  // ---- 实时提取最新回复中的图表 ----
  const lastAssistantContent = useMemo(() => {
    const assistantMsgs = messages.filter((m) => m.role === 'assistant' && m.content)
    return assistantMsgs.length > 0 ? assistantMsgs[assistantMsgs.length - 1].content : ''
  }, [messages])

  const contentDiagrams = useMemo(() => extractDiagrams(lastAssistantContent), [lastAssistantContent])

  // 合并 SSE 推送的图表 + 从内容中提取的图表
  const allDiagrams = useMemo(() => {
    const existingCharts = new Set(knowledgeDiagrams.map((d) => d.chart))
    const merged = [...knowledgeDiagrams]
    contentDiagrams.forEach((d) => {
      if (!existingCharts.has(d.chart)) {
        merged.push(d)
        existingCharts.add(d.chart)
      }
    })
    return merged
  }, [knowledgeDiagrams, contentDiagrams])

  // ---- 发送消息时重置知识面板 ----
  const handleSend = useCallback((text) => {
    setKnowledgeDiagrams([])
    setKnowledgeReferences([])
    sendMessage(text)
  }, [sendMessage])

  // ---- 初始化 ----
  useEffect(() => { loadSessions(); loadResources(); loadPath() }, [])

  // ---- 会话相关 ----
  async function loadSessions() {
    setLoadingSessions(true)
    try {
      const data = await getTutorSessions(studentId)
      setSessions(Array.isArray(data) ? data : data?.sessions || [])
    } catch {
      if (USE_MOCK) {
        setSessions([
          { id: 's1', title: '二次函数答疑', updatedAt: new Date(), messageCount: 12 },
          { id: 's2', title: '英语语法解惑', updatedAt: new Date(Date.now() - 86400000), messageCount: 8 },
        ])
      }
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
      if (USE_MOCK) {
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
      }
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
      if (USE_MOCK) { setTimeout(() => { setPathData(mockPath); setPathLoading(false) }, 400); return }
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
      message.error('生成失败')
      if (USE_MOCK) setPathData(mockPath)
    } finally { setGenerating(false) }
  }

  // ---- 路径时间线数据 ----
  const stages = pathData?.stages || []

  // ==================== 右侧面板底部：资源 & 路径 ====================
  const bottomCollapseItems = [
    {
      key: 'resources',
      label: <span><BookOutlined /> 学习资源</span>,
      children: (
        <div style={{ maxHeight: 300, overflowY: 'auto' }}>
          <Space wrap style={{ marginBottom: 8 }}>
            <Input
              placeholder="搜索资源..."
              prefix={<SearchOutlined />}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onPressEnter={handleSearch}
              style={{ width: 140 }}
              size="small"
              allowClear
            />
            <Select
              value={type}
              onChange={setType}
              options={TYPE_OPTIONS}
              style={{ width: 100 }}
              size="small"
            />
            <Button type="primary" size="small" icon={<FilterOutlined />} onClick={handleSearch}>筛选</Button>
          </Space>

          {resLoading ? (
            <LoadingSkeleton type="card" count={2} />
          ) : resources.length === 0 ? (
            <Empty description="没有找到符合条件的资源" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <>
              <Row gutter={[8, 8]}>
                {resources.map((r) => (
                  <Col span={24} key={r.id}>
                    <ResourceCard resource={r} onClick={setPreview} onDownload={(r) => console.log('Download:', r.id)} />
                  </Col>
                ))}
              </Row>
              {resTotal > pageSize && (
                <div style={{ textAlign: 'center', marginTop: 8 }}>
                  <Pagination current={page} pageSize={pageSize} total={resTotal} onChange={setPage} size="small" showSizeChanger={false} />
                </div>
              )}
            </>
          )}

          {/* 资源预览 */}
          {preview && (
            <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: 12, marginTop: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <Text strong style={{ fontSize: 13 }}>预览：{preview.title}</Text>
                <Button size="small" onClick={() => setPreview(null)}>关闭</Button>
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
        <div style={{ maxHeight: 300, overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <Text strong style={{ fontSize: 13 }}>{pathData?.title || '我的学习路径'}</Text>
            <Button
              type="primary" size="small" icon={<PlusOutlined />}
              onClick={handleGeneratePath} loading={generating}
            >
              {generating ? '生成中...' : '生成'}
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
            <Empty description="还没有学习路径" image={Empty.PRESENTED_IMAGE_SIMPLE} />
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

      {/* ---- 中部：左-右分栏 ---- */}
      <div style={{ flex: 1, minHeight: 0, display: 'flex', gap: 0 }}>
        {/* ---- 左侧：对话区 ---- */}
        <div style={{
          flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column',
          border: '1px solid var(--border, #f0f0f0)',
          borderRadius: 12,
          background: 'var(--bg-card, #fff)',
          overflow: 'hidden',
        }}>
          {/* 解释风格选择器 */}
          <div style={{
            flexShrink: 0,
            padding: '10px 16px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex', justifyContent: 'center',
            background: '#fafbfc',
          }}>
            <Segmented
              value={explanationStyle}
              onChange={setExplanationStyle}
              options={EXPLANATION_STYLES}
              size="small"
            />
          </div>

          {/* ChatBox */}
          <div style={{ flex: 1, minHeight: 0 }}>
            <ChatBox
              messages={messages}
              isLoading={isLoading}
              onSend={handleSend}
              onAbort={abort}
              placeholder={activeSessionId ? '输入你的问题...' : '请先选择或创建会话'}
              showEmpty={false}
            />
          </div>
        </div>

        {/* ---- 右侧：知识面板 + 资源/路径 ---- */}
        <div style={{
          width: 380, flexShrink: 0, marginLeft: 12,
          display: 'flex', flexDirection: 'column',
          border: '1px solid var(--border, #f0f0f0)',
          borderRadius: 12,
          overflow: 'hidden',
          background: 'var(--bg-card, #fff)',
        }}>
          {/* 知识面板 */}
          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
            <KnowledgePanel
              diagrams={allDiagrams}
              references={knowledgeReferences}
              explanationStyle={explanationStyle}
              loading={isLoading}
            />
          </div>

          {/* 底部：学习资源 & 学习路径（折叠） */}
          <div style={{
            flexShrink: 0,
            borderTop: '1px solid var(--border, #f0f0f0)',
            maxHeight: '45%',
            overflowY: 'auto',
          }}>
            <Collapse
              ghost
              size="small"
              defaultActiveKey={[]}
              items={bottomCollapseItems}
              style={{ background: 'transparent' }}
            />
          </div>
        </div>
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
