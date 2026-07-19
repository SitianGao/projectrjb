import { useState, useCallback, useRef, useEffect } from 'react'
import { streamSse } from '../utils/sseClient'
import { useTypewriter } from './useTypewriter'

export const PHASE = {
  COLLECTING: 'collecting',
  READY: 'ready',
  PLANNING: 'planning',
  GENERATING: 'generating',
  ACTIVE: 'active',
  FAILED: 'failed',
}

/**
 * 通用对话 Hook — 统一 SSE 流式 + 打字机。
 *
 * @param {Object} options
 * @param {Function} options.streamFetcher - (message, signal, sendOptions) => Promise<Response>
 * @param {Array} options.initialMessages
 * @param {Function} options.onProfileUpdate
 * @param {Function} options.onSSEEvent
 * @param {Function} options.onPhaseChange
 */
export function useChat({
  streamFetcher,
  initialMessages = [],
  initialCompleteness = 0,
  initialPhase = PHASE.COLLECTING,
  onProfileUpdate,
  onSSEEvent,
  onPhaseChange,
} = {}) {
  const [messages, setMessages] = useState(initialMessages)
  const [isLoading, setIsLoading] = useState(false)

  // ── 画像状态 ──
  const [completeness, setCompleteness] = useState(initialCompleteness)

  // ── 阶段状态机 ──
  const [phase, setPhase] = useState(initialPhase)
  const phaseRef = useRef(initialPhase)
  const userConfirmedRef = useRef(
    initialPhase === PHASE.READY || initialPhase === PHASE.PLANNING ||
    initialPhase === PHASE.GENERATING || initialPhase === PHASE.ACTIVE,
  )

  const updatePhase = useCallback((newPhase) => {
    setPhase(newPhase)
    phaseRef.current = newPhase
    onPhaseChange?.(newPhase)
  }, [onPhaseChange])

  // ── 统一打字机 ──
  const typewriter = useTypewriter()

  // 画像达到阈值 → READY
  useEffect(() => {
    if (userConfirmedRef.current) return
    if (phaseRef.current !== PHASE.COLLECTING) return
    const hasUserMsg = messages.some((m) => m.role === 'user')
    const hasRealReply = messages.some(
      (m) => m.role === 'assistant' && m.content && !m.id?.startsWith('welcome'),
    )
    if (hasUserMsg && hasRealReply && !isLoading && Number(completeness || 0) >= 0.75) {
      updatePhase(PHASE.READY)
    }
  }, [messages, isLoading, completeness, updatePhase])

  const abortRef = useRef(null)
  const idCounter = useRef(0)

  const nextId = useCallback(() => {
    idCounter.current += 1
    return `msg-${Date.now()}-${idCounter.current}`
  }, [])

  const sendMessage = useCallback(
    async (content, options = {}) => {
      if (!content?.trim() || !streamFetcher) return

      const userMsg = { id: nextId(), role: 'user', content }
      const assistantId = nextId()
      const assistantMsg = { id: assistantId, role: 'assistant', content: '' }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      typewriter.reset()
      setIsLoading(true)

      const controller = new AbortController()
      abortRef.current = controller

      try {
        await streamSse(
          () => streamFetcher(content, controller.signal, options),
          {
            onDelta: (text) => {
              typewriter.push(text)
              // Also update the raw messages array for completeness tracking
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: m.content + text } : m,
                ),
              )
            },
            onData: (event) => {
              // Forward structured events (diagrams, references, profile_update, etc.)
              if (event.type === 'profile_update' || event.profile) {
                const profileData =
                  event.data ||
                  event.profile?.profile ||
                  event.profile ||
                  (event.dimensions ? event : null)
                if (profileData && onProfileUpdate) {
                  onProfileUpdate(profileData)
                }
              }
              onSSEEvent?.(event)
            },
            onError: (err) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId && !m.content
                    ? { ...m, content: err.message || 'AI 服务暂时不可用', error: true }
                    : m,
                ),
              )
            },
            onDone: () => {
              typewriter.flush()
            },
            signal: controller.signal,
          },
        )
      } catch (err) {
        if (err.name !== 'AbortError') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId && !m.content
                ? { ...m, content: '请求失败，请重试', error: true }
                : m,
            ),
          )
        }
      } finally {
        typewriter.flush()
        setIsLoading(false)
        abortRef.current = null
      }
    },
    [streamFetcher, nextId, onProfileUpdate, onSSEEvent, typewriter],
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    typewriter.reset()
  }, [typewriter])

  const abort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  // ── Build displayedMessages from typewriter state ──
  // The last assistant message's content is replaced with the typewriter display
  const displayedMessages = (() => {
    const msgs = [...messages]
    if (msgs.length === 0) return msgs
    const last = msgs[msgs.length - 1]
    if (last.role === 'assistant' && isLoading && typewriter.display) {
      msgs[msgs.length - 1] = { ...last, content: typewriter.display }
    }
    return msgs
  })()

  return {
    messages: displayedMessages,
    isLoading,
    sendMessage,
    clearMessages,
    abort,
    setMessages,
  }
}
