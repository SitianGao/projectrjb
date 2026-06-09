import { useState, useCallback, useRef } from 'react'

/**
 * 通用对话 Hook
 *
 * 管理消息列表、发送消息、流式接收回复。
 * 不绑定具体 API —— 调用方传入 streamFetcher 来对接不同后端。
 *
 * @param {Object} options
 * @param {Function} options.streamFetcher - (message: string, signal?: AbortSignal) => Promise<Response>
 *   发起流式请求，返回 fetch Response。body 应为 SSE 流或纯文本流。
 * @param {Array} options.initialMessages - 初始消息列表
 * @returns {{
 *   messages: Array<{id, role, content}>,
 *   isLoading: boolean,
 *   sendMessage: (content: string) => Promise<void>,
 *   clearMessages: () => void,
 *   abort: () => void,
 * }}
 */
export function useChat({ streamFetcher, initialMessages = [] } = {}) {
  const [messages, setMessages] = useState(initialMessages)
  const [isLoading, setIsLoading] = useState(false)
  const abortRef = useRef(null)
  const idCounter = useRef(0)

  const nextId = useCallback(() => {
    idCounter.current += 1
    return `msg-${Date.now()}-${idCounter.current}`
  }, [])

  const sendMessage = useCallback(
    async (content) => {
      if (!content?.trim() || !streamFetcher) return

      const userMsg = { id: nextId(), role: 'user', content }
      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)

      const assistantId = nextId()
      // 先插入一条空的 assistant 消息用于流式填充
      setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', content: '' }])

      const controller = new AbortController()
      abortRef.current = controller

      try {
        const response = await streamFetcher(content, controller.signal)

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
              const delta =
                parsed.choices?.[0]?.delta?.content ||
                parsed.content ||
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
    [streamFetcher, nextId],
  )

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  const abort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { messages, isLoading, sendMessage, clearMessages, abort, setMessages }
}
