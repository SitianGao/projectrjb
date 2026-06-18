import { useRef, useEffect, useCallback, useState, useMemo } from 'react'
import { Input, Button, Space, Avatar, Typography, Spin, Tooltip, Segmented } from 'antd'
import {
  SendOutlined,
  UserOutlined,
  RobotOutlined,
  StopOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons'
import MarkdownRenderer from './MarkdownRenderer'
import { useTheme } from '../contexts/ThemeContext'

const { Text } = Typography

// ========== Mock ==========
const MOCK_MESSAGES = [
  {
    id: 'm1', role: 'assistant',
    content: '你好！我是你的学习助手，让我们来聊聊你的学习情况吧。\n\n你可以告诉我：\n- 你的年级\n- 你擅长或不擅长的科目\n- 你的学习目标\n- 你喜欢的的学习方式',
  },
  { id: 'm2', role: 'user', content: '你好！我是初三的学生，我数学还不错，但英语比较吃力。我希望能考上重点高中。' },
  {
    id: 'm3', role: 'assistant',
    content: '了解了！你的情况很清楚：\n\n**优势**：数学基础扎实 👍\n**薄弱**：英语需要加强 📖\n**目标**：冲刺重点高中 🎯\n\n我建议先从这几个方向入手：\n\n1. **数学**：挑战压轴题，争取拿满分\n2. **英语**：每天坚持单词背诵 + 阅读训练',
  },
  { id: 'm4', role: 'user', content: '我更喜欢通过做题来学习，不太喜欢看视频。' },
  {
    id: 'm5', role: 'assistant',
    content: '明白了！你属于**实践型学习者**。\n\n基于你的情况，我制定了以下策略：\n\n| 维度 | 策略 |\n|------|------|\n| 数学 | 每日 3-5 道压轴题 + 错题复盘 |\n| 英语 | 每日 30 个单词 + 1 篇阅读理解 |\n| 综合 | 每周一次模拟测试 |\n\n这个方案你觉得怎么样？😊',
  },
]

// ========== 动画注入 ==========
let keyframesInjected = false
function injectKeyframes() {
  if (keyframesInjected || typeof document === 'undefined') return
  const style = document.createElement('style')
  style.textContent = `
    @keyframes msgSlideIn {
      from { opacity: 0; transform: translateY(12px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes dotBounce {
      0%, 80%, 100% { transform: translateY(0); }
      40% { transform: translateY(-6px); }
    }
    @keyframes inputGlow {
      0%, 100% { box-shadow: 0 0 0 0 rgba(139,92,246,0.2); }
      50% { box-shadow: 0 0 0 4px rgba(139,92,246,0.06); }
    }
    .chat-msg-enter { animation: msgSlideIn 0.35s ease-out; }
  `
  document.head.appendChild(style)
  keyframesInjected = true
}

// ========== 思考动画 ==========
function ThinkingDots() {
  return (
    <span style={{ display: 'inline-flex', gap: 5, alignItems: 'center', height: 20 }}>
      {[0, 1, 2].map((i) => (
        <span key={i} style={{
          width: 7, height: 7, borderRadius: '50%',
          background: 'linear-gradient(135deg, #aa3bff, #6366f1)',
          animation: `dotBounce 1.2s ${i * 0.18}s infinite ease-in-out`,
          display: 'inline-block',
        }} />
      ))}
    </span>
  )
}

// ========== 解释风格选项 ==========
const STYLE_OPTIONS = [
  { label: '💡 类比', value: 'analogy' },
  { label: '📐 公式', value: 'formula' },
  { label: '📊 图解', value: 'diagram' },
  { label: '📖 故事', value: 'story' },
]

// ========== 主组件 ==========
export default function ChatBox({
  messages = MOCK_MESSAGES,
  isLoading = false,
  onSend,
  onAbort,
  placeholder = '输入你的问题...',
  showEmpty = true,
  emptyText = '开始一段对话吧',
  suggestions = [],
  onSuggestionClick,
  defaultStyle = 'analogy',
  showStyleSelector = true,
}) {
  const { resolved } = useTheme()
  const isDark = resolved === 'dark'

  const listRef = useRef(null)
  const [inputValue, setInputValue] = useState('')
  const [showScrollBtn, setShowScrollBtn] = useState(false)
  const [focused, setFocused] = useState(false)
  const [style, setStyle] = useState(defaultStyle)

  useEffect(() => { injectKeyframes() }, [])

  const isNearBottom = useCallback(() => {
    const el = listRef.current
    if (!el) return true
    return el.scrollHeight - el.scrollTop - el.clientHeight < 80
  }, [])

  const scrollToBottom = useCallback((smooth = false) => {
    const el = listRef.current
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'instant' })
  }, [])

  useEffect(() => {
    if (isNearBottom()) scrollToBottom(false)
  }, [messages, isNearBottom, scrollToBottom])

  useEffect(() => {
    const el = listRef.current
    if (!el) return
    const h = () => setShowScrollBtn(!isNearBottom())
    el.addEventListener('scroll', h, { passive: true })
    h()
    return () => el.removeEventListener('scroll', h)
  }, [isNearBottom])

  const handleSend = useCallback(() => {
    const text = inputValue.trim()
    if (!text || isLoading) return
    onSend?.(text, { style })
    setInputValue('')
    setTimeout(() => scrollToBottom(false), 60)
  }, [inputValue, isLoading, onSend, scrollToBottom, style])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }, [handleSend])

  const showStreaming = useMemo(() =>
    isLoading && messages.length > 0 &&
    messages[messages.length - 1]?.role === 'assistant' &&
    !messages[messages.length - 1]?.content,
  [isLoading, messages])

  const isEmpty = messages.length === 0

  return (
    <div className="chatbox" style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg-card)', position: 'relative' }}>
      {/* 解释风格选择器 — 置顶 */}
      {showStyleSelector && (
        <div style={{
          borderBottom: '1px solid var(--border)',
          padding: '10px 24px',
          background: 'var(--bg-card)',
          flexShrink: 0,
          display: 'flex', justifyContent: 'center',
          position: 'relative', zIndex: 2,
        }}>
          <Segmented
            value={style}
            onChange={setStyle}
            options={STYLE_OPTIONS}
            size="small"
            style={{
              background: 'var(--input-bar-bg, #f5f5f5)',
              padding: 3,
              borderRadius: 10,
            }}
          />
        </div>
      )}

      {/* 消息列表 */}
      <div ref={listRef} className="chatbox-list" style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', minHeight: 0 }}>
        {isEmpty && showEmpty ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 300 }}>
            <div style={{
              width: 72, height: 72, borderRadius: 20,
              background: isDark
                ? 'linear-gradient(135deg, rgba(139,92,246,0.1) 0%, rgba(22,119,255,0.08) 100%)'
                : 'linear-gradient(135deg, #f0e6ff 0%, #e6f0ff 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 20,
            }}>
              <RobotOutlined style={{ fontSize: 34, color: '#8b5cf6' }} />
            </div>
            <Text style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>有什么可以帮你的？</Text>
            <Text type="secondary" style={{ fontSize: 13, marginBottom: 20 }}>{emptyText}</Text>

            {suggestions.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', maxWidth: 460 }}>
                {suggestions.map((s, i) => (
                  <div
                    key={i}
                    onClick={() => onSuggestionClick?.(s, { style })}
                    style={{
                      padding: '8px 16px', borderRadius: 20, fontSize: 13,
                      background: 'var(--bg-card)', border: '1px solid var(--border)',
                      cursor: 'pointer', transition: 'all 0.2s',
                      color: 'var(--text-secondary)',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#8b5cf6'; e.currentTarget.style.color = '#8b5cf6' }}
                    onMouseLeave={(e) => { e.currentTarget.style.borderColor = ''; e.currentTarget.style.color = '' }}
                  >
                    {s}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div style={{ maxWidth: 800, margin: '0 auto', width: '100%' }}>
            <Space direction="vertical" size={20} style={{ width: '100%' }}>
              {messages.map((msg) => {
                const isUser = msg.role === 'user'
                return (
                  <div key={msg.id} className="chat-msg-enter" style={{
                    display: 'flex', gap: 12,
                    flexDirection: isUser ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                  }}>
                    <Avatar
                      size={36}
                      icon={isUser ? <UserOutlined /> : <RobotOutlined />}
                      style={{
                        flexShrink: 0,
                        background: isUser
                          ? 'linear-gradient(135deg, #1677ff, #4096ff)'
                          : 'linear-gradient(135deg, #8b5cf6, #6366f1)',
                        boxShadow: isUser
                          ? '0 2px 8px rgba(22,119,255,0.25)'
                          : '0 2px 8px rgba(139,92,246,0.25)',
                      }}
                    />

                    <div style={{
                      maxWidth: '75%',
                      padding: '12px 18px',
                      borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                      background: isUser
                        ? 'var(--msg-user-bg)'
                        : 'var(--msg-bubble-bg)',
                      border: isUser
                        ? '1px solid var(--msg-user-border)'
                        : '1px solid var(--msg-bubble-border)',
                      boxShadow: isUser ? 'none' : (isDark ? 'none' : '0 1px 3px rgba(0,0,0,0.04)'),
                    }}>
                      {isUser ? (
                        <Text style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: '1.6' }}>{msg.content}</Text>
                      ) : (
                        msg.error ? (
                          <div>
                            <Text type="danger" style={{ fontSize: 13 }}>⚠️ {msg.error}</Text>
                            {msg.content && <div style={{ marginTop: 8, opacity: 0.5 }}><MarkdownRenderer content={msg.content} compact /></div>}
                          </div>
                        ) : (
                          <div className="assistant-msg"><MarkdownRenderer content={msg.content} compact /></div>
                        )
                      )}
                    </div>
                  </div>
                )
              })}

              {showStreaming && (
                <div className="chat-msg-enter" style={{ paddingLeft: 48, display: 'flex', alignItems: 'center', gap: 10 }}>
                  <ThinkingDots />
                  <Text type="secondary" style={{ fontSize: 13 }}>思考中...</Text>
                </div>
              )}

              {isLoading && !showStreaming && (
                <div style={{ paddingLeft: 48, display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Spin size="small" />
                  <Text type="secondary" style={{ fontSize: 13 }}>生成中...</Text>
                </div>
              )}
            </Space>
          </div>
        )}
      </div>

      {/* 回到底部 */}
      {showScrollBtn && (
        <div style={{ position: 'absolute', bottom: 80, left: '50%', transform: 'translateX(-50%)', zIndex: 10 }}>
          <Button shape="circle" icon={<ArrowDownOutlined />} onClick={() => scrollToBottom(true)}
            style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.12)', opacity: 0.9 }} />
        </div>
      )}

      {/* 输入区 */}
      <div style={{
        borderTop: '1px solid var(--border)', padding: '14px 24px 16px',
        background: 'var(--bg-card)',
        flexShrink: 0,
        borderRadius: '0 0 12px 12px',
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto', width: '100%' }}>
          <div style={{
            display: 'flex', gap: 8, alignItems: 'flex-end',
            background: 'var(--input-bar-bg)', borderRadius: 12, padding: '6px 6px 6px 16px',
            border: '1.5px solid transparent',
            transition: 'border-color 0.2s, box-shadow 0.2s',
            ...(focused ? { borderColor: '#8b5cf6', boxShadow: isDark ? '0 0 0 3px rgba(139,92,246,0.15)' : '0 0 0 3px rgba(139,92,246,0.08)' } : {}),
          }}>
            <Input.TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder={placeholder}
              autoSize={{ minRows: 1, maxRows: 4 }}
              disabled={isLoading}
              variant="borderless"
              style={{ flex: 1, background: 'transparent', resize: 'none', padding: '4px 0', fontSize: 14 }}
            />
            {isLoading ? (
              <Button danger shape="circle" icon={<StopOutlined />} onClick={onAbort} size="middle" />
            ) : (
              <Button
                type="primary" shape="circle" icon={<SendOutlined />}
                onClick={handleSend} disabled={!inputValue.trim()} size="middle"
                style={{
                  background: inputValue.trim() ? 'linear-gradient(135deg, #8b5cf6, #6366f1)' : '#d9d9d9',
                  border: 'none', flexShrink: 0,
                }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
