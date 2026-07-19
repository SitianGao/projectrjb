import { useState, useCallback, useRef, useEffect } from 'react'
import { Button, Input, Space, Tag, Typography, Spin } from 'antd'
import {
  BulbOutlined,
  FormOutlined,
  ReloadOutlined,
  RobotOutlined,
  SendOutlined,
  HighlightOutlined,
} from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import MarkdownRenderer from './MarkdownRenderer'

const { Text } = Typography

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
    if (codeBlockMatch) {
      jsonStr = codeBlockMatch[1].trim()
    }
    const start = jsonStr.indexOf('{')
    const end = jsonStr.lastIndexOf('}')
    if (start >= 0 && end > start) {
      jsonStr = jsonStr.slice(start, end + 1)
    }
    const parsed = JSON.parse(jsonStr)
    if (typeof parsed === 'object' && parsed !== null) {
      const keys = ['answer', 'content', 'text', 'response', 'message', 'explanation']
      for (const key of keys) {
        if (typeof parsed[key] === 'string' && parsed[key].length > 5) {
          return parsed[key]
        }
      }
    }
  } catch {
    // Not valid JSON, try regex fallback
  }

  // Try 2: regex extraction for common answer keys
  const answerMatch = trimmed.match(/"(?:answer|content|text|response|message|explanation)"\s*:\s*"((?:[^"\\]|\\.)*)"/)
  if (answerMatch && answerMatch[1] && answerMatch[1].length > 5) {
    return answerMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\')
  }

  // Try 3: find the longest string value in the JSON
  const allStrings = trimmed.match(/"((?:[^"\\]|\\.)*)"/g)
  if (allStrings) {
    let best = ''
    for (const s of allStrings) {
      const unquoted = s.slice(1, -1)
      if (unquoted.length > best.length && !unquoted.startsWith('{') && !unquoted.startsWith('[')) {
        best = unquoted
      }
    }
    if (best.length > 10) {
      return best.replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\')
    }
  }

  return text
}

const QUICK_ACTIONS = [
  { key: 'explain', icon: <HighlightOutlined />, label: '解释选中内容' },
  { key: 'example', icon: <FormOutlined />, label: '生成例题' },
  { key: 'another', icon: <ReloadOutlined />, label: '换一种方式讲解' },
  { key: 'check', icon: <BulbOutlined />, label: '检查我的理解' },
]

function getSuggestedQuestions(topic) {
  if (!topic || topic === '学习任务') {
    return ['当前学习内容的核心要点是什么？', '能给我一个例子帮助理解吗？', '这些知识之间有什么联系？']
  }
  return [
    `什么是${topic}的核心概念？`,
    `能给我一个关于${topic}的具体例子吗？`,
    `${topic}常见的误区有哪些？`,
    `${topic}和之前学的内容有什么联系？`,
  ]
}

/**
 * Right sidebar — AI tutor panel with quick actions,
 * suggested questions, and chat input.
 */
export default function AITutorPanel({
  currentTopic,
  currentContent,
  style,
}) {
  const { studentId } = useAuth()
  const questions = getSuggestedQuestions(currentTopic)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addMessage = useCallback((role, content) => {
    setMessages((prev) => [...prev, { role, content, id: Date.now() }])
  }, [])

  const handleSend = useCallback(async (text) => {
    const msg = text || input.trim()
    if (!msg || sending) return
    setInput('')
    setSending(true)
    addMessage('user', msg)

    try {
      // Use fetch-based SSE for tutor response
      const response = await fetch('/api/tutor/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
        },
        body: JSON.stringify({
          student_id: studentId,
          message: [
            currentTopic ? `当前知识点：${currentTopic}` : '',
            currentContent ? `当前学习内容摘要：${String(currentContent).slice(0, 600)}` : '',
            `学生问题：${msg}`,
          ].filter(Boolean).join('\n\n'),
          explanation_style: 'auto',
          top_k: 3,
        }),
      })

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response stream')

      let fullContent = ''
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''  // Keep incomplete line in buffer

        for (const raw of lines) {
          const line = raw.trim()
          if (!line) continue
          if (!line.startsWith('data: ')) continue

          const data = line.slice(6).trim()
          if (data === '[DONE]' || data === '[STOP]') continue

          try {
            const json = JSON.parse(data)
            const type = json.type || json.event || ''

            // Handle delta/token events (main streaming content)
            if (type === 'delta' || type === 'token' || type === 'text') {
              const chunk = json.text || json.delta || json.content || ''
              if (chunk) fullContent += chunk
            }
            // Handle data/result events (structured response)
            else if ((type === 'data' || type === 'result') && json.content) {
              // Only use if we haven't accumulated delta content
              if (!fullContent) {
                fullContent = json.content
              }
            }
            // Handle chat events (legacy)
            else if (type === 'chat' && json.content) {
              fullContent += json.content
            }
            // Skip done/start/progress events
            else if (type === 'done' || type === 'close' || type === 'complete' ||
                     type === 'start' || type === 'progress') {
              // ignore
            }
            // Unknown type with content
            else if (json.content && typeof json.content === 'string') {
              fullContent += json.content
            }
          } catch {
            // Plain text fallback
            if (data && data !== '[DONE]' && data !== '[STOP]') {
              fullContent += data
            }
          }
        }
      }

      if (fullContent) {
        addMessage('assistant', fullContent)
      } else {
        addMessage('assistant', '抱歉，我暂时无法回答这个问题。请换个方式提问。')
      }
    } catch {
      addMessage('assistant', '网络请求失败，请稍后重试。')
    } finally {
      setSending(false)
    }
  }, [input, sending, studentId, currentTopic, currentContent, addMessage])

  const handleQuickAction = useCallback((key) => {
    const prompts = {
      explain: `请详细解释一下「${currentTopic || '这个知识点'}」`,
      example: `请为「${currentTopic || '这个知识点'}」生成一个具体的例题`,
      another: `请用不同的方式重新讲解「${currentTopic || '这个知识点'}」`,
      check: `请出1-2道题检查我对「${currentTopic || '当前内容'}」的掌握程度`,
    }
    handleSend(prompts[key] || '')
  }, [currentTopic, handleSend])

  return (
    <div style={{
      width: 320, minWidth: 320,
      background: '#FFFFFF', borderRadius: 16,
      border: '1px solid #E5E7EB',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      ...style,
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid #E5E7EB',
        display: 'flex', alignItems: 'center', gap: 10,
        background: '#F9F7FF',
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: 12,
          background: '#6C5CE7', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 18,
        }}>
          <RobotOutlined />
        </div>
        <div>
          <Text strong style={{ fontSize: 14, color: '#111827' }}>AI 导师</Text>
          {currentTopic && (
            <Tag color="purple" style={{ marginLeft: 6, fontSize: 11, borderRadius: 6 }}>
              {currentTopic.length > 8 ? currentTopic.slice(0, 8) + '…' : currentTopic}
            </Tag>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #F3F4F6' }}>
        <div style={{ fontSize: 11, color: '#9CA3AF', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
          快捷操作
        </div>
        <Space size={6} wrap>
          {QUICK_ACTIONS.map((action) => (
            <Button
              key={action.key}
              size="small"
              icon={action.icon}
              onClick={() => handleQuickAction(action.key)}
              disabled={sending}
              style={{
                borderRadius: 8,
                borderColor: '#E5E7EB',
                color: '#6B7280',
                fontSize: 12,
              }}
            >
              {action.label}
            </Button>
          ))}
        </Space>
      </div>

      {/* Chat Messages */}
      <div style={{
        flex: 1, overflow: 'auto', padding: '12px 16px',
        display: 'flex', flexDirection: 'column', gap: 10,
      }}>
        {messages.length === 0 && (
          <div style={{ padding: '8px 0' }}>
            <div style={{ fontSize: 11, color: '#9CA3AF', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              推荐问题
            </div>
            {questions.map((q, i) => (
              <button
                key={i}
                onClick={() => handleSend(q)}
                disabled={sending}
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  padding: '10px 14px', marginBottom: 6,
                  borderRadius: 10, border: '1px solid #E5E7EB',
                  background: '#FAFAFC', cursor: 'pointer',
                  fontSize: 13, color: '#374151',
                  fontFamily: 'inherit',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#F3F0FF'
                  e.currentTarget.style.borderColor = '#6C5CE7'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = '#FAFAFC'
                  e.currentTarget.style.borderColor = '#E5E7EB'
                }}
              >
                <BulbOutlined style={{ marginRight: 8, color: '#6C5CE7', fontSize: 12 }} />
                {q}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '90%',
              padding: '10px 14px',
              borderRadius: msg.role === 'user' ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
              background: msg.role === 'user' ? '#6C5CE7' : '#F3F0FF',
              color: msg.role === 'user' ? '#FFFFFF' : '#111827',
              fontSize: 13,
              lineHeight: 1.5,
              wordBreak: 'break-word',
            }}
          >
            {msg.role === 'assistant' ? <MarkdownRenderer content={stripJsonWrapper(msg.content)} compact /> : msg.content}
          </div>
        ))}
        {sending && (
          <div style={{ padding: '8px 14px', fontSize: 13, color: '#9CA3AF' }}>
            <Spin size="small" /> AI 导师思考中...
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: '12px 16px', borderTop: '1px solid #E5E7EB',
        display: 'flex', gap: 8,
        background: '#FAFAFC',
      }}>
        <Input.TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder="向 AI 导师提问..."
          autoSize={{ minRows: 1, maxRows: 3 }}
          disabled={sending}
          style={{
            borderRadius: 10,
            borderColor: '#E5E7EB',
            fontSize: 13,
            resize: 'none',
          }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={() => handleSend()}
          loading={sending}
          style={{
            borderRadius: 10,
            background: '#6C5CE7',
            borderColor: '#6C5CE7',
            alignSelf: 'flex-end',
          }}
        />
      </div>
    </div>
  )
}
