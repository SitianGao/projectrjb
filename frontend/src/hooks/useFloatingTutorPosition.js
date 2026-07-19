import { useState, useCallback, useEffect, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'

const DEFAULT_POS = { right: 24, bottom: 80 }
const MIN_BOTTOM = 60
const PADDING_TOP = 80

function getPositionKey(studentId) {
  return studentId ? `tutorPosition:${studentId}` : 'tutorPosition:default'
}

function loadPosition(studentId) {
  try {
    const raw = localStorage.getItem(getPositionKey(studentId))
    if (!raw) return { ...DEFAULT_POS }
    const parsed = JSON.parse(raw)
    return {
      right: typeof parsed.right === 'number' ? parsed.right : DEFAULT_POS.right,
      bottom: typeof parsed.bottom === 'number' ? parsed.bottom : DEFAULT_POS.bottom,
    }
  } catch {
    return { ...DEFAULT_POS }
  }
}

function savePosition(studentId, pos) {
  try {
    localStorage.setItem(getPositionKey(studentId), JSON.stringify(pos))
  } catch { /* ignore quota errors */ }
}

export default function useFloatingTutorPosition(studentId) {
  const [position, setPosition] = useState(() => loadPosition(studentId))
  const draggingRef = useRef(false)
  const startYRef = useRef(0)
  const startBottomRef = useRef(0)

  // reload if studentId changes
  useEffect(() => {
    setPosition(loadPosition(studentId))
  }, [studentId])

  const constrain = useCallback((bottom) => {
    const maxBottom = Math.max(MIN_BOTTOM, window.innerHeight - 120)
    return Math.min(maxBottom, Math.max(MIN_BOTTOM, bottom))
  }, [])

  const clampInsideViewport = useCallback(() => {
    setPosition((prev) => {
      const next = { ...prev, bottom: constrain(prev.bottom) }
      savePosition(studentId, next)
      return next
    })
  }, [studentId, constrain])

  // re-clamp on window resize
  useEffect(() => {
    window.addEventListener('resize', clampInsideViewport)
    return () => window.removeEventListener('resize', clampInsideViewport)
  }, [clampInsideViewport])

  const handlePointerDown = useCallback((e) => {
    draggingRef.current = true
    startYRef.current = e.clientY
    startBottomRef.current = position.bottom
    e.target.setPointerCapture(e.pointerId)
  }, [position.bottom])

  const handlePointerMove = useCallback((e) => {
    if (!draggingRef.current) return
    const deltaY = startYRef.current - e.clientY
    const nextBottom = constrain(startBottomRef.current + deltaY)
    setPosition((prev) => ({ ...prev, bottom: nextBottom }))
  }, [constrain])

  const handlePointerUp = useCallback(() => {
    if (!draggingRef.current) return
    draggingRef.current = false
    setPosition((prev) => {
      const clamped = { ...prev, bottom: constrain(prev.bottom) }
      savePosition(studentId, clamped)
      return clamped
    })
  }, [studentId, constrain])

  return {
    position,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
  }
}
