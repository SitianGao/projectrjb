import { useState, useCallback, useRef, useEffect } from 'react'

/**
 * 画像阶段状态机
 *
 *   collecting   — 正在收集画像 (首次对话中)
 *   ready        — 首次对话完成，等待用户确认
 *   planning     — 正在生成学习路径
 *   generating   — 路径完成，资源/任务生成中
 *   active       — 学习旅程可用
 *   failed       — 流程失败，可重试
 */
export const PHASE = {
  COLLECTING: 'collecting',
  READY: 'ready',
  PLANNING: 'planning',
  GENERATING: 'generating',
  ACTIVE: 'active',
  FAILED: 'failed',
}

/**
 * 通用对话 Hook
 *
 * 管理消息列表、发送消息、流式接收回复。
 * 不绑定具体 API —— 调用方传入 streamFetcher 来对接不同后端。
 *
 * @param {Object} options
 * @param {Function} options.streamFetcher - (message: string, signal?: AbortSignal, sendOptions?: object) => Promise<Response>
 *   发起流式请求，返回 fetch Response。body 应为 SSE 流或纯文本流。sendOptions 为 sendMessage 透传的附加参数。
 * @param {Array} options.initialMessages - 初始消息列表
 * @param {Function} options.onProfileUpdate - (profile: object) => void
 *   当 SSE 返回 profile_update 事件时回调，传入更新后的画像数据
 * @param {Function} options.onSSEEvent - (event: object) => void
 *   当 SSE 返回其他结构化事件时回调
 * @param {string} options.initialPhase - 初始阶段（用于页面刷新恢复）
 * @param {number} options.initialCompleteness - 初始完整度（用于页面刷新恢复）
 * @param {Function} options.onPhaseChange - (phase: string) => void  阶段变化回调
 * @returns {{
 *   messages: Array<{id, role, content}>,
 *   rawMessages: Array<{id, role, content}>,
 *   isLoading: boolean,
 *   sendMessage: (content: string, options?: object) => Promise<void>,
 *   clearMessages: () => void,
 *   abort: () => void,
 *   setMessages: (messages) => void,
 *   profile: object | null,
 *   completeness: number | null,
 *   nextQuestions: string[],
 *   error: { message: string } | null,
 *   retryLastMessage: () => void,
 *   phase: string,
 *   setPhase: (phase: string) => void,
 * }}
 */
export function useChat({ streamFetcher, initialMessages = [], onProfileUpdate, onSSEEvent, initialPhase = PHASE.COLLECTING, initialCompleteness = null, onPhaseChange } = {}) {
  const [messages, setMessages] = useState(initialMessages)
  const [displayedMessages, setDisplayedMessages] = useState(initialMessages)
  const [isLoading, setIsLoading] = useState(false)

  // ── 画像相关状态 ──
  const [profile, setProfile] = useState(null)
  const [completeness, setCompleteness] = useState(initialCompleteness)
  const [nextQuestions, setNextQuestions] = useState([])
  const [error, setError] = useState(null)

  // ── 阶段状态机 ──
  const [phase, setPhase] = useState(initialPhase)
  const phaseRef = useRef(initialPhase)
  // 标记用户是否已经确认过（避免 ready 状态被后续对话覆盖为 collecting）
  const userConfirmedRef = useRef(initialPhase === PHASE.READY || initialPhase === PHASE.PLANNING || initialPhase === PHASE.GENERATING || initialPhase === PHASE.ACTIVE)

  // 包装 setPhase，同步更新 ref 并通知外部
  const updatePhase = useCallback((newPhase) => {
    setPhase(newPhase)
    phaseRef.current = newPhase
    onPhaseChange?.(newPhase)
  }, [onPhaseChange])

  // ── 用户首次对话完成后自动进入 ready ──
  // 只要用户发送了至少一条消息并收到回复，即可开启学习之旅
  useEffect(() => {
    if (userConfirmedRef.current) return
    if (phaseRef.current !== PHASE.COLLECTING) return

    const hasUserMsg = messages.some(m => m.role === 'user')
    const hasRealReply = messages.some(
      m => m.role === 'assistant' && m.content && !m.id?.startsWith('welcome'),
    )

    if (hasUserMsg && hasRealReply && !isLoading) {
      updatePhase(PHASE.READY)
    }
  }, [messages, isLoading, updatePhase])

  const abortRef = useRef(null)
  const idCounter = useRef(0)
  const typewriterTimerRef = useRef(null)
  const displayedPosRef = useRef(0)

  // 保存最近一次用户消息及其选项，用于重试
  const lastUserMessageRef = useRef(null)

  const nextId = useCallback(() => {
    idCounter.current += 1
    return `msg-${Date.now()}-${idCounter.current}`
  }, [])

  // ========== 逐字打字机动画 ==========
  useEffect(() => {
    const clearTimer = () => {
      if (typewriterTimerRef.current) {
        clearInterval(typewriterTimerRef.current)
        typewriterTimerRef.current = null
      }
    }

    if (!isLoading) {
      // 流式结束 → 立即同步全部内容
      setDisplayedMessages(messages)
      displayedPosRef.current = 0
      clearTimer()
      return
    }

    // 找到正在流式填充的 assistant 消息
    const lastMsg = messages[messages.length - 1]
    if (!lastMsg || lastMsg.role !== 'assistant') {
      clearTimer()
      return
    }

    const targetContent = lastMsg.content
    const targetLen = targetContent.length

    if (displayedPosRef.current >= targetLen) {
      clearTimer()
      return
    }

    clearTimer()

    typewriterTimerRef.current = setInterval(() => {
      if (displayedPosRef.current >= targetLen) {
        clearTimer()
        return
      }

      const lag = targetLen - displayedPosRef.current
      const charsPerTick = lag > 30 ? 2 : 1
      displayedPosRef.current += charsPerTick
      if (displayedPosRef.current > targetLen) {
        displayedPosRef.current = targetLen
      }

      setDisplayedMessages((prev) => {
        const updated = [...prev]
        const last = { ...updated[updated.length - 1] }
        last.content = targetContent.slice(0, displayedPosRef.current)
        updated[updated.length - 1] = last
        return updated
      })
    }, 25)

    return clearTimer
  }, [messages, isLoading])

  // ========== 构建发送给后端的 history ==========
  // 后端期望 List[str]，格式为 "用户: xxx" / "助手: xxx"
  const buildHistory = useCallback(() => {
    return messages
      .filter((m) => m.role === 'user' || (m.role === 'assistant' && m.content && !m.error))
      .map((m) => {
        const roleLabel = m.role === 'user' ? '用户' : '助手'
        return `${roleLabel}: ${m.content}`
      })
  }, [messages])

  const sendMessage = useCallback(
    async (content, options = {}) => {
      if (!content?.trim() || !streamFetcher) return

      const userMsg = { id: nextId(), role: 'user', content }
      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)
      // 重置打字机位置
      displayedPosRef.current = 0
      // 清除之前的错误
      setError(null)

      // 记录用于重试
      lastUserMessageRef.current = { content, options }

      const assistantId = nextId()
      // 先插入一条空的 assistant 消息用于流式填充
      setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', content: '' }])

      const controller = new AbortController()
      abortRef.current = controller

      try {
        // buildHistory 读取的是上一轮渲染的 messages（新加的 user/assistant 尚未更新到 state）
        // 所以直接全部作为历史传给后端，无需 slice
        const history = buildHistory()

        const response = await streamFetcher(content, controller.signal, {
          ...options,
          history,
          current_profile: profile,
        })

        if (!response || !response.body) {
          throw new Error('不支持流式响应')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // 处理 SSE 格式: data: <json>\n\n
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const data = line.slice(6).trim()
            if (data === '[DONE]') continue

            try {
              const parsed = JSON.parse(data)

              switch (parsed.type) {
                // ── chat: LLM 自然语言回复增量 ──
                case 'chat': {
                  const delta =
                    parsed.content ||
                    parsed.delta ||
                    parsed.choices?.[0]?.delta?.content ||
                    ''
                  if (delta) {
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === assistantId ? { ...m, content: m.content + delta } : m,
                      ),
                    )
                  }
                  break
                }

                // ── profile_update: 画像更新 ──
                case 'profile_update': {
                  // 兼容多种返回格式：
                  // { profile: { ... }, completeness: 0.8, next_questions: [...] }
                  // { data: { profile: {...}, completeness: 0.8 } }
                  // { profile: { student_id, profile: {...} } }   (nested)
                  const profileData =
                    parsed.data?.profile ||
                    parsed.profile?.profile ||
                    parsed.profile ||
                    parsed.data ||
                    null

                  if (profileData && typeof profileData === 'object' && !Array.isArray(profileData)) {
                    setProfile((prev) => {
                      const merged = { ...prev, ...profileData }
                      onProfileUpdate?.(merged)
                      return merged
                    })
                  }

                  // 解析 completeness（兼容外层和嵌套）
                  const comp =
                    parsed.completeness ??
                    parsed.data?.completeness ??
                    parsed.profile?.completeness ??
                    parsed.data?.profile?.completeness ??
                    null
                  if (comp !== null && comp !== undefined) {
                    const num = typeof comp === 'number' ? comp : parseFloat(comp)
                    if (!isNaN(num)) {
                      setCompleteness(num)
                    }
                  }

                  // 解析 next_questions
                  const questions =
                    parsed.next_questions ??
                    parsed.data?.next_questions ??
                    []
                  if (Array.isArray(questions) && questions.length > 0) {
                    setNextQuestions(questions)
                  }
                  break
                }

                // ── error: 后端返回错误 ──
                case 'error': {
                  const errMsg = parsed.message || parsed.error || '服务端错误'
                  setError({ message: errMsg, source: 'server' })
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId
                        ? { ...m, error: errMsg }
                        : m,
                    ),
                  )
                  break
                }

                // ── done: 本轮 SSE 流正常结束 ──
                // 仅表示流结束，不直接视为画像完成
                case 'done':
                  break

                // ── 默认：兼容 OpenAI 格式及自定义事件 ──
                default: {
                  // 尝试提取内容增量
                  const delta =
                    parsed.content ||
                    parsed.choices?.[0]?.delta?.content ||
                    parsed.delta ||
                    ''
                  if (delta) {
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === assistantId ? { ...m, content: m.content + delta } : m,
                      ),
                    )
                  }

                  // 通知外部回调（diagrams/references 等结构化数据）
                  onSSEEvent?.(parsed)
                }
              }
            } catch {
              // 非 JSON，作为纯文本追加
              if (data) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: m.content + data } : m,
                  ),
                )
              }
            }
          }
        }
      } catch (err) {
        // AbortError 是用户主动取消，不算错误
        if (err.name !== 'AbortError') {
          const errorMessage = err.message || '请求失败，请重试'
          setError({ message: errorMessage, source: 'network' })
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content || '', error: errorMessage }
                : m,
            ),
          )
        } else {
          // 用户取消，保留已有内容
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId && !m.content
                ? { ...m, content: '已取消' }
                : m,
            ),
          )
        }
      } finally {
        setIsLoading(false)
        abortRef.current = null
      }
    },
    [streamFetcher, nextId, onProfileUpdate, onSSEEvent, profile, buildHistory],
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    setDisplayedMessages([])
    displayedPosRef.current = 0
    setProfile(null)
    setCompleteness(null)
    setNextQuestions([])
    setError(null)
  }, [])

  const abort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  // 重试最近一次失败的消息
  const retryLastMessage = useCallback(() => {
    const last = lastUserMessageRef.current
    if (!last) return

    // 移除失败的 assistant 回复（最后一条）
    setMessages((prev) => {
      const lastMsg = prev[prev.length - 1]
      if (lastMsg?.role === 'assistant' && lastMsg?.error) {
        return prev.slice(0, -2) // 移除 user + error assistant
      }
      return prev
    })
    setError(null)
    // 重新发送
    sendMessage(last.content, last.options)
  }, [sendMessage])

  // 用户确认开启学习之旅：从 ready → planning
  const confirmJourney = useCallback(() => {
    if (phaseRef.current !== PHASE.READY) return
    userConfirmedRef.current = true
    updatePhase(PHASE.PLANNING)
  }, [updatePhase])

  // 外部可直接设置阶段（如 planning → generating → active → failed）
  const setPhaseExternal = useCallback((newPhase) => {
    if (newPhase === PHASE.READY || newPhase === PHASE.PLANNING || newPhase === PHASE.GENERATING || newPhase === PHASE.ACTIVE) {
      userConfirmedRef.current = true
    }
    // 回到 collecting 时重置确认标记，允许再次触发 ready
    if (newPhase === PHASE.COLLECTING) {
      userConfirmedRef.current = false
    }
    updatePhase(newPhase)
  }, [updatePhase])

  return {
    messages: displayedMessages,
    rawMessages: messages,
    isLoading,
    sendMessage,
    clearMessages,
    abort,
    setMessages,
    profile,
    completeness,
    nextQuestions,
    error,
    retryLastMessage,
    phase,
    setPhase: setPhaseExternal,
    confirmJourney,
  }
}
