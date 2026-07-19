import { useState, useCallback, useRef } from 'react'

/**
 * 打字机效果 Hook — 模拟逐字输出。
 *
 * 用法：
 *   const { display, push, reset, flush } = useTypewriter({ speed: 30 })
 *
 *   收到 token → push(text)
 *   结束时     → flush()
 *   新一轮     → reset()
 *   渲染       → <p>{display}</p>
 */

const DEFAULT_SPEED = 25 // 毫秒/字

export function useTypewriter({ speed = DEFAULT_SPEED } = {}) {
  const [display, setDisplay] = useState('')
  const bufferRef = useRef('')
  const queueRef = useRef([])
  const timerRef = useRef(null)
  const posRef = useRef(0)

  const pump = useCallback(() => {
    if (timerRef.current) return
    timerRef.current = setInterval(() => {
      const all = bufferRef.current + queueRef.current.join('')
      if (posRef.current < all.length) {
        posRef.current += 1
        setDisplay(all.slice(0, posRef.current))
      } else {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }, speed)
  }, [speed])

  const push = useCallback((text) => {
    queueRef.current.push(text)
    pump()
  }, [pump])

  const reset = useCallback(() => {
    clearInterval(timerRef.current)
    timerRef.current = null
    bufferRef.current = ''
    queueRef.current = []
    posRef.current = 0
    setDisplay('')
  }, [])

  const flush = useCallback(() => {
    bufferRef.current += queueRef.current.join('')
    queueRef.current = []
    clearInterval(timerRef.current)
    timerRef.current = null
    const all = bufferRef.current
    posRef.current = all.length
    setDisplay(all)
  }, [])

  return { display, push, reset, flush }
}
