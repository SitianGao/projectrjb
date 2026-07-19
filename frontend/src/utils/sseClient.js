/**
 * SSE 流式客户端 — 统一的 Server-Sent Events 解析器。
 *
 * 用法：
 *   await streamSse(fetchPromise, { onDelta, onData, onError, onDone, onStart, onProgress })
 *
 * SSE 事件类型：
 *   - delta / token  → onDelta(text)
 *   - data / result  → onData(event)
 *   - error          → onError(err)
 *   - done / close   → onDone()
 *   - start          → onStart(event)
 *   - progress       → onProgress(event)
 */

const SSE_EVENT_REGEX = /^data:\s?(.*)$/

/**
 * @param {Promise<Response>|(() => Promise<Response>)} fetchInput Response 对象或返回 Response 的工厂函数
 * @param {Object} opts
 * @param {(text: string) => void} [opts.onDelta]
 * @param {(event: {type: string, [key]: any}) => void} [opts.onData]
 * @param {(err: {code?: string, message: string}) => void} [opts.onError]
 * @param {() => void} [opts.onDone]
 * @param {(event: any) => void} [opts.onStart]
 * @param {(event: any) => void} [opts.onProgress]
 */
export async function streamSse(fetchInput, opts = {}) {
  const { onDelta, onData, onError, onDone, onStart, onProgress } = opts

  let response
  try {
    response = typeof fetchInput === 'function' ? await fetchInput() : await fetchInput
  } catch (err) {
    onError?.({ code: 'NETWORK', message: err.message || '网络请求失败' })
    return
  }

  if (!response.ok) {
    let detail = ''
    try {
      const body = await response.clone().text()
      detail = body.slice(0, 200)
    } catch (_) { /* ignore */ }
    onError?.({ code: `HTTP_${response.status}`, message: detail || `请求失败 (${response.status})` })
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    // 不是流式响应，当作普通 JSON 处理
    try {
      const json = await response.clone().json()
      onData?.(json)
      onDone?.()
    } catch (_) {
      onError?.({ code: 'PARSE', message: '无法解析响应' })
    }
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''
  let started = false

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      // 最后一个可能是不完整的行，保留在 buffer
      buffer = lines.pop() || ''

      for (const raw of lines) {
        const line = raw.trim()
        if (!line) continue

        const match = line.match(SSE_EVENT_REGEX)
        if (!match) continue

        const data = match[1].trim()
        if (data === '[DONE]' || data === '[STOP]') {
          onDone?.()
          return
        }

        // 尝试解析 JSON
        try {
          const event = JSON.parse(data)
          const type = event.type || event.event || ''

          if (!started) {
            started = true
            onStart?.(event)
          }

          switch (type) {
            case 'start':
              onStart?.(event)
              break
            case 'progress':
              onProgress?.(event)
              break
            case 'delta':
            case 'token':
            case 'text':
              onDelta?.(event.text || event.delta || event.content || '')
              break
            case 'data':
            case 'result':
              onData?.(event)
              break
            case 'error':
              onError?.({ code: event.code, message: event.message || '服务器错误' })
              break
            case 'done':
            case 'close':
            case 'complete':
              onDone?.()
              return
            default:
              // 未知类型，当作 data 处理
              onData?.(event)
          }
        } catch (_) {
          // 纯文本行，当作 delta
          onDelta?.(data)
        }
      }
    }

    // 处理残留 buffer
    if (buffer.trim()) {
      const line = buffer.trim()
      if (line !== '[DONE]' && line !== '[STOP]') {
        onDelta?.(line)
      }
    }

    onDone?.()
  } catch (err) {
    if (err.name === 'AbortError') {
      // 正常中断
      onDone?.()
    } else {
      onError?.({ code: 'STREAM', message: err.message || '流读取中断' })
    }
  } finally {
    try { reader.releaseLock() } catch (_) { /* ignore */ }
  }
}
