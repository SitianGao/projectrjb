import { useState, useCallback, useRef, useEffect } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { Button, Input, Tag, Typography, Tooltip } from 'antd'
import {
  RobotOutlined,
  SendOutlined,
  CloseOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import { useTutorContext } from '../contexts/TutorContext.jsx'
import useFloatingTutorPosition from '../hooks/useFloatingTutorPosition'
import useFloatingTutorChat from '../hooks/useFloatingTutorChat'
import MarkdownRenderer from './MarkdownRenderer'
import './FloatingTutor.css'

const { Text } = Typography

// ── route visibility ──
const HIDDEN_PATTERNS = [
  /^\/login/, /^\/register/, /^\/forgot-password/,
  /^\/profile/, /^\/edit-profile/, /^\/change-password/,
  /^\/onboarding/, /^\/home$/, /^\/docs/,
  /\/ai-workspace/,
]

function shouldShowFloatingTutor(pathname) {
  return !HIDDEN_PATTERNS.some((p) => p.test(pathname))
}

function buildQuickQuestions(topic) {
  const base = [
    { key: 'simple', label: '用更简单的话解释' },
    { key: 'life', label: '给我举一个生活中的例子' },
    { key: 'formula', label: '解释当前公式' },
    { key: 'quiz', label: '针对这个知识点出一道题' },
    { key: 'summary', label: '总结本页重点' },
    { key: 'weakness', label: '根据我的薄弱点重新讲解' },
  ]
  if (topic) {
    base[0] = { ...base[0], label: `用更简单的话解释「${topic.slice(0, 18)}」` }
    base[3] = { ...base[3], label: `针对「${topic.slice(0, 18)}」出一道题` }
  }
  return base
}

const DIALOG_W = 380
const DIALOG_H = 480

/**
 * Last-resort JSON stripping: if the content looks like JSON,
 * try to extract the readable answer text from it.
 */
function stripJsonWrapper(text) {
  if (!text || typeof text !== 'string') return text
  const trimmed = text.trim()
  if (!trimmed.startsWith('{') && !trimmed.startsWith('```')) return text

  // Try 1: JSON.parse
  try {
    let jsonStr = trimmed
    const codeBlockMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)```/)
    if (codeBlockMatch) jsonStr = codeBlockMatch[1].trim()
    const start = jsonStr.indexOf('{')
    const end = jsonStr.lastIndexOf('}')
    if (start >= 0 && end > start) jsonStr = jsonStr.slice(start, end + 1)
    const parsed = JSON.parse(jsonStr)
    if (typeof parsed === 'object' && parsed !== null) {
      const keys = ['answer', 'content', 'text', 'response', 'message', 'explanation']
      for (const key of keys) {
        if (typeof parsed[key] === 'string' && parsed[key].length > 5) return parsed[key]
      }
    }
  } catch {}

  // Try 2: regex for common answer keys
  const m = trimmed.match(/"(?:answer|content|text|response|message|explanation)"\s*:\s*"((?:[^"\\]|\\.)*)"/)
  if (m && m[1] && m[1].length > 5) return m[1].replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\')

  // Try 3: longest string value
  const all = trimmed.match(/"((?:[^"\\]|\\.)*)"/g)
  if (all) {
    let best = ''
    for (const s of all) { const u = s.slice(1, -1); if (u.length > best.length && !u.startsWith('{') && !u.startsWith('[')) best = u }
    if (best.length > 10) return best.replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\')
  }

  return text
}

export default function FloatingTutor() {
  const location = useLocation()
  const params = useParams()
  const { activeCourse } = useAuth()
  const { context } = useTutorContext()

  const studentId = activeCourse?.student_id || 'demo-student-ai-dl'
  const courseId = params.courseId || context?.courseId || activeCourse?.id
  const stageId = params.stageId || context?.stageId
  const taskId = params.taskId || context?.taskId

  const courseTitle = activeCourse?.title || context?.courseTitle || ''
  const stageTitle = context?.stageTitle || ''
  const taskTitle = context?.taskTitle || context?.topic || ''
  const topic = context?.topic || taskTitle || ''
  const learningGoal = activeCourse?.goal || context?.learningGoal || ''

  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const inputRef = useRef(null)
  const messagesEndRef = useRef(null)
  const ballRef = useRef(null)

  const { position, handlePointerDown, handlePointerMove, handlePointerUp } =
    useFloatingTutorPosition(studentId)

  const {
    messages, loading, sendMessage, clearMessages,
  } = useFloatingTutorChat({
    studentId, courseId, stageId, taskId,
    courseTitle, stageTitle, taskTitle, topic, learningGoal,
    profileData: context?.profileData,
  })

  const quickQuestions = buildQuickQuestions(topic)

  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      setTimeout(() => inputRef.current?.focus(), 200)
    }
  }, [messages, open])

  const handleSend = useCallback(() => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    sendMessage(text)
  }, [input, loading, sendMessage])

  const handleQuickQuestion = useCallback((q) => {
    sendMessage(q.label)
  }, [sendMessage])

  useEffect(() => {
    window.__floatingTutorAsk = (selectedText, prompt) => {
      if (!selectedText) return
      setOpen(true)
      const msg = prompt
        ? `${prompt}\n\n我不理解这句话，请结合当前课程内容解释：\n"${selectedText}"`
        : `我不理解这句话，请结合当前课程内容解释：\n"${selectedText}"`
      setTimeout(() => sendMessage(msg, { selectedText }), 400)
    }
    return () => { delete window.__floatingTutorAsk }
  }, [sendMessage])

  const visible = shouldShowFloatingTutor(location.pathname)
  if (!visible) return null

  // dialog position: prefer above the ball, fall below if not enough room
  const ballBottom = position.bottom
  const ballRight = position.right
  const dialogBottom = Math.min(ballBottom + 64 + DIALOG_H, window.innerHeight - 16) > window.innerHeight - DIALOG_H
    ? ballBottom + 64
    : Math.max(8, window.innerHeight - DIALOG_H - 16)
  const dialogStyle = {
    position: 'fixed',
    right: Math.max(8, ballRight - (DIALOG_W - 56)),
    bottom: ballBottom + 64 > window.innerHeight - DIALOG_H ? 16 : ballBottom + 64,
    width: DIALOG_W,
    maxHeight: DIALOG_H,
    zIndex: 1001,
  }

  return (
    <>
      {/* ── floating icon ── */}
      {!open && (
        <div
          ref={ballRef}
          className="floating-tutor-ball"
          style={{
            position: 'fixed',
            right: position.right,
            bottom: position.bottom,
            zIndex: 1000,
          }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
        >
          <Tooltip title="遇到不懂的内容？问问 AI 导师" placement="left">
            <div className="floating-tutor-icon" onClick={() => setOpen(true)}>
              <RobotOutlined style={{ fontSize: 28 }} />
            </div>
          </Tooltip>
        </div>
      )}

      {/* ── floating dialog ── */}
      {open && (
        <div className="floating-tutor-dialog" style={dialogStyle}>
          {/* header */}
          <div className="ft-dialog-header">
            <div className="ft-dialog-header-left">
              <RobotOutlined style={{ color: '#8b5cf6', fontSize: 18 }} />
              <Text strong style={{ fontSize: 14 }}>AI 导师</Text>
              {taskTitle && (
                <Tag color="blue" style={{ margin: 0, fontSize: 11, lineHeight: '20px' }}>
                  {taskTitle.slice(0, 12)}
                </Tag>
              )}
            </div>
            <Button
              type="text" size="small" icon={<CloseOutlined />}
              onClick={() => { setOpen(false); clearMessages() }}
            />
          </div>

          {/* quick questions */}
          {messages.length === 0 && (
            <div className="ft-dialog-quick">
              {quickQuestions.map((q) => (
                <span
                  key={q.key}
                  className="ft-quick-chip"
                  onClick={() => handleQuickQuestion(q)}
                >
                  {q.label}
                </span>
              ))}
            </div>
          )}

          {/* messages */}
          <div className="ft-dialog-messages">
            {messages.length === 0 && (
              <div className="ft-dialog-empty">
                <MessageOutlined style={{ fontSize: 32, color: '#e8e8e8' }} />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  我是你的 AI 导师，基于当前学习内容为你答疑
                </Text>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`ft-msg ${msg.role === 'user' ? 'ft-msg-user' : 'ft-msg-ai'}`}>
                {msg.role === 'assistant' ? <MarkdownRenderer content={stripJsonWrapper(msg.content)} compact /> : msg.content}
              </div>
            ))}
            {loading && <div className="ft-msg ft-msg-ai">⋯</div>}
            <div ref={messagesEndRef} />
          </div>

          {/* input */}
          <div className="ft-dialog-input">
            <Input.TextArea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); handleSend() } }}
              placeholder="问 AI 导师…"
              autoSize={{ minRows: 1, maxRows: 3 }}
              disabled={loading}
              style={{ borderRadius: 10 }}
            />
            <Button
              type="primary" size="small" icon={<SendOutlined />}
              onClick={handleSend} loading={loading} disabled={!input.trim()}
              style={{ borderRadius: 10, marginLeft: 6 }}
            />
          </div>
        </div>
      )}
    </>
  )
}
