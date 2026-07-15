/**
 * Profile Chat Mock —— 模拟 SSE 流式对话，不依赖后端
 *
 * 产出符合后端格式的 SSE 事件流：
 *   data: {"type":"chat","content":"..."}
 *   data: {"type":"profile_update","profile":{...}}
 *   data: {"type":"done"}
 */

// ── 模拟回复模板（按学生输入关键词匹配） ──
const REPLY_TEMPLATES = [
  {
    keywords: ['数学', '高数', '微积分', '线代', '概率'],
    reply: '了解了！数学相关课程确实需要扎实的基础。你目前的数学水平大概在什么阶段呢？是刚开始接触还是有一定基础了？',
    profile: { knowledge_level: '初级', learning_goal: '掌握数学基础概念', cognitive_style: '偏好公式推导', weakness: ['数学推导'], interest: ['概率与统计'], pace_preference: '中速均衡型' },
  },
  {
    keywords: ['编程', 'python', '代码', 'java', 'c++', '前端', '后端'],
    reply: '编程学习最重要的是动手实践！你是想从零开始学一门语言，还是想深入某个特定方向呢？',
    profile: { knowledge_level: '初级', learning_goal: '掌握编程基础', cognitive_style: '偏好动手和代码示例', weakness: [], interest: ['代码案例', '项目实战'], pace_preference: '中速均衡型' },
  },
  {
    keywords: ['目标', '想学', '计划', '希望', '打算'],
    reply: '有明确的目标是学习的第一步！你能再具体说说想达到什么程度吗？比如通过某个考试、完成一个项目、还是掌握某个技能？',
    profile: { knowledge_level: '中级', learning_goal: '完成实践项目', cognitive_style: '偏好图解与案例', weakness: [], interest: ['项目实战'], pace_preference: '中速均衡型' },
  },
  {
    keywords: ['hello', 'hi', '你好', '开始', 'help'],
    reply: '你好！很高兴成为你的学习伙伴 🎓\n\n为了更好地了解你，请告诉我：\n1. 你目前的学习阶段（高中/大学/工作）？\n2. 你想提升什么科目或技能？\n3. 你更喜欢看书、看视频、还是动手做题？',
    profile: { knowledge_level: '初级', learning_goal: '探索学习方向', cognitive_style: '视觉型（偏好视频/图解）', weakness: [], interest: [], pace_preference: '中速均衡型' },
  },
  {
    keywords: ['考试', '复习', '备考', '刷题'],
    reply: '备考复习需要有计划地进行。你准备的是什么考试呢？有没有特别薄弱的知识点需要重点突破？',
    profile: { knowledge_level: '中级', learning_goal: '通过考试/认证', cognitive_style: '偏好动手和代码示例', weakness: ['知识点碎片化'], interest: [], pace_preference: '快速概览型' },
  },
  {
    keywords: ['工作', '职场', '转行', '提升', '加薪'],
    reply: '职场提升需要结合工作场景来学习，这样效率最高。你目前从事哪个行业？想往哪个方向发展？',
    profile: { knowledge_level: '中高级', learning_goal: '职场技能提升', cognitive_style: '偏好动手和代码示例', weakness: [], interest: ['行业前沿技术'], pace_preference: '快速概览型' },
  },
]

// ── 默认回复 ──
const DEFAULT_REPLY = '明白了！你提到的这些信息对我很有帮助。能再详细说说你具体想学习的内容吗？比如你对什么领域最感兴趣？有没有特别想攻克的知识难点？'
const DEFAULT_PROFILE = { knowledge_level: '初级', learning_goal: '探索学习方向', cognitive_style: '视觉型（偏好视频/图解）', weakness: [], interest: [], pace_preference: '中速均衡型' }

// ── 根据对话轮数计算 completeness ──
const COMPLETENESS_BY_ROUND = [0.25, 0.45, 0.60, 0.72, 0.82, 0.88, 0.92, 0.95]

// ── 全局会话状态（模拟多轮对话） ──
let roundCount = 0

/** 重置 mock 会话（页面刷新/清空时调用） */
export function resetMockChat() {
  roundCount = 0
}

/** 生成下一个问题的建议 */
function pickNextQuestions(profile) {
  const questions = []
  if (!profile.weakness?.length) questions.push('你觉得学习中最容易卡住的地方是什么？')
  if (!profile.interest?.length) questions.push('有没有特别感兴趣的领域或技术方向？')
  if (!profile.learning_goal || profile.learning_goal === '探索学习方向') questions.push('你希望通过学习达到什么具体目标？')
  if (questions.length < 2) questions.push('你更喜欢通过什么方式学习（看视频、读书、做题）？')
  return questions.slice(0, 3)
}

/**
 * 生成 mock SSE 事件流
 *
 * @param {string} message - 用户消息
 * @param {object} options - { history, current_profile }
 * @returns {ReadableStream} SSE 流
 */
export function createMockChatStream(message, options = {}) {
  roundCount += 1
  const round = roundCount

  // ── 匹配回复模板 ──
  const msg = message.toLowerCase()
  const matched = REPLY_TEMPLATES.find((t) =>
    t.keywords.some((kw) => msg.includes(kw)),
  )
  const { reply, profile } = matched || { reply: DEFAULT_REPLY, profile: DEFAULT_PROFILE }

  // ── 计算 completeness ──
  const completeness = COMPLETENESS_BY_ROUND[Math.min(round - 1, COMPLETENESS_BY_ROUND.length - 1)]

  // ── 下一轮追问 ──
  const nextQuestions = completeness < 0.85 ? pickNextQuestions(profile) : []

  // ── 构建 SSE 事件 ──
  const profileResult = {
    student_id: 'demo-student-01',
    profile,
    completeness,
    confidence: 0.6 + completeness * 0.3,
    sources: ['mock_dialogue'],
    next_questions: nextQuestions,
  }

  const chatEvent = JSON.stringify({ type: 'chat', content: reply })
  const profileEvent = JSON.stringify({ type: 'profile_update', profile: profileResult })
  const doneEvent = JSON.stringify({ type: 'done' })

  // ── 模拟增量流式输出 ──
  const chars = reply.split('')
  const chunks = []
  let i = 0
  while (i < chars.length) {
    const step = Math.floor(Math.random() * 5) + 3
    chunks.push(chars.slice(i, i + step).join(''))
    i += step
  }

  // 将 chat 内容拆成多个增量 delta，最后一个是完整 reply
  const events = []
  // 先发增量（模拟打字）
  for (let j = 0; j < chunks.length - 1; j++) {
    events.push(`data: ${JSON.stringify({ type: 'chat', content: chunks[j], delta: chunks[j] })}\n\n`)
  }
  // 最后一个增量 + profile + done
  if (chunks.length > 0) {
    events.push(`data: ${JSON.stringify({ type: 'chat', content: chunks[chunks.length - 1], delta: chunks[chunks.length - 1] })}\n\n`)
  }
  events.push(`data: ${profileEvent}\n\n`)
  events.push(`data: ${doneEvent}\n\n`)

  const encoder = new TextEncoder()
  let eventIdx = 0

  return new ReadableStream({
    async pull(controller) {
      if (eventIdx < events.length) {
        // 模拟网络延迟：每个片段间隔 40-120ms
        const delay = 40 + Math.random() * 80
        await new Promise((resolve) => setTimeout(resolve, delay))
        controller.enqueue(encoder.encode(events[eventIdx]))
        eventIdx++
      } else {
        controller.close()
      }
    },
  })
}
