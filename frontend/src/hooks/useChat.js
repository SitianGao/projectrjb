import { useState, useCallback, useRef, useEffect } from 'react'

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
 *   当 SSE 返回结构化事件（含 diagrams/references 等字段）时回调
 * @returns {{
 *   messages: Array<{id, role, content}>,
 *   isLoading: boolean,
 *   sendMessage: (content: string, options?: object) => Promise<void>,
 *   clearMessages: () => void,
 *   abort: () => void,
 * }}
 */
export function useChat({ streamFetcher, initialMessages = [], onProfileUpdate, onSSEEvent } = {}) {
  const [messages, setMessages] = useState(initialMessages)
  const [displayedMessages, setDisplayedMessages] = useState(initialMessages)
  const [isLoading, setIsLoading] = useState(false)
<<<<<<< Updated upstream
=======

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

  // ── 画像达到后端统一门槛后自动进入 ready ──
  // 与 backend/config.py 的 PROFILE_READY_THRESHOLD 保持一致，避免过早
  // 展示“开启学习之旅”，随后又被后端以画像不完整拒绝。
  useEffect(() => {
    if (userConfirmedRef.current) return
    if (phaseRef.current !== PHASE.COLLECTING) return

    const hasUserMsg = messages.some(m => m.role === 'user')
    const hasRealReply = messages.some(
      m => m.role === 'assistant' && m.content && !m.id?.startsWith('welcome'),
    )

    if (
      hasUserMsg &&
      hasRealReply &&
      !isLoading &&
      Number(completeness || 0) >= 0.85
    ) {
      updatePhase(PHASE.READY)
    }
  }, [messages, isLoading, completeness, updatePhase])

>>>>>>> Stashed changes
  const abortRef = useRef(null)
  const idCounter = useRef(0)
  const typewriterTimerRef = useRef(null)
  const displayedPosRef = useRef(0)

  const nextId = useCallback(() => {
    idCounter.current += 1
    return `msg-${Date.now()}-${idCounter.current}`
  }, [])

  // ========== 逐字打字机动画 ==========
  useEffect(() => {
    // 清理前一个定时器
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

    // 如果内容没变且已经追上了，不需要重新启动定时器
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

      // 自适应速度：落后较多时快一些，接近时逐字出现
      const lag = targetLen - displayedPosRef.current
      const charsPerTick = lag > 30 ? 2 : 1
      displayedPosRef.current += charsPerTick
      // 防止越界
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
    }, 25) // ~25ms/tick

    return clearTimer
  }, [messages, isLoading])

  const sendMessage = useCallback(
    async (content, options = {}) => {
      if (!content?.trim() || !streamFetcher) return

      const userMsg = { id: nextId(), role: 'user', content }
      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)
      // 重置打字机位置
      displayedPosRef.current = 0

      const assistantId = nextId()
      // 先插入一条空的 assistant 消息用于流式填充
      setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', content: '' }])

      const controller = new AbortController()
      abortRef.current = controller

      try {
        const response = await streamFetcher(content, controller.signal, options)

        if (!response.body) {
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

              // 处理 profile_update 事件
              if (parsed.type === 'profile_update' && onProfileUpdate) {
                // 兼容多种返回格式：
                // { profile: { student_id, profile: {...}, ... } }
                // { profile: {...} }
                // { data: {...} }
                const profileData =
                  parsed.data ||
                  (parsed.profile?.profile) ||
                  parsed.profile ||
                  (parsed.dimensions ? parsed : null)
                if (profileData) {
                  onProfileUpdate(profileData)
                }
                continue
              }

              // 通知外部回调（diagrams/references 等结构化数据）
              if (onSSEEvent) {
                onSSEEvent(parsed)
              }

              // 跳过无内容的事件（如 type:start, type:done）
              if (parsed.type === 'start' || parsed.type === 'done') continue

              // 优先匹配后端自定义格式，保留 OpenAI 兼容
              const delta =
                parsed.content ||
                parsed.choices?.[0]?.delta?.content ||
                parsed.delta ||
                (typeof parsed === 'string' ? parsed : '')

              if (delta) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: m.content + delta } : m,
                  ),
                )
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
        if (err.name !== 'AbortError') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content || '请求失败，请重试', error: true }
                : m,
            ),
          )
        }
      } finally {
        setIsLoading(false)
        abortRef.current = null
      }
    },
    [streamFetcher, nextId, onProfileUpdate, onSSEEvent],
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    setDisplayedMessages([])
    displayedPosRef.current = 0
  }, [])

  const abort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { messages: displayedMessages, isLoading, sendMessage, clearMessages, abort, setMessages }
}
