import { useRef, useEffect, useCallback, useState, useMemo } from 'react'
import { Input, Button, Space, Avatar, Typography, Spin, Empty, Tooltip } from 'antd'
import {
  SendOutlined,
  UserOutlined,
  RobotOutlined,
  StopOutlined,
  DownOutlined,
} from '@ant-design/icons'
import MarkdownRenderer from './MarkdownRenderer'

const { Text } = Typography

// ========== Mock 对话数据 ==========
const MOCK_MESSAGES = [
  {
    id: 'm1',
    role: 'assistant',
    content:
      '你好！我是你的学习助手，让我们来聊聊你的学习情况吧。\n\n你可以告诉我：\n- 你的年级\n- 你擅长或不擅长的科目\n- 你的学习目标\n- 你喜欢的的学习方式（比如：看视频、读书、做题等）',
  },
  {
    id: 'm2',
    role: 'user',
    content: '你好！我是初三的学生，我数学还不错，但英语比较吃力。我希望能考上重点高中。',
  },
  {
    id: 'm3',
    role: 'assistant',
    content:
      '了解了！你的情况很清楚：\n\n**优势**：数学基础扎实 👍\n**薄弱**：英语需要加强 📖\n**目标**：冲刺重点高中 🎯\n\n根据你的情况，我建议先从这几个方向入手：\n\n1. **数学**：可以挑战一些压轴题，争取拿满分\n2. **英语**：建议每天坚持单词背诵 + 阅读训练\n3. **学习方式**：你更喜欢做题还是看视频讲解呢？',
  },
  {
    id: 'm4',
    role: 'user',
    content: '我更喜欢通过做题来学习，不太喜欢看视频。',
  },
  {
    id: 'm5',
    role: 'assistant',
    content:
      '明白了！你属于 **实践型学习者**（Learning by Doing），通过做题来掌握知识对你来说更高效。\n\n基于你的偏好和学习情况，我为你制定了以下学习策略：\n\n| 维度 | 策略 |\n|------|------|\n| 数学 | 每日 3-5 道压轴题 + 错题复盘 |\n| 英语 | 每日 30 个单词 + 1 篇阅读理解 |\n| 综合 | 每周一次模拟测试，跟踪进步 |\n\n这个方案你觉得怎么样？可以根据你的反馈继续调整 😊',
  },
]

// ========== 样式常量 ==========
const BUBBLE_STYLE = {
  user: {
    bg: '#e6f4ff',
    border: '1px solid rgba(22,119,255,0.15)',
    avatarBg: '#1677ff',
    avatarShadow: '0 2px 8px rgba(22,119,255,0.25)',
  },
  assistant: {
    bg: 'rgba(170,59,255,0.06)',
    border: '1px solid rgba(170,59,255,0.18)',
    avatarBg: '#aa3bff',
    avatarShadow: '0 2px 8px rgba(170,59,255,0.3)',
    bubbleShadow: '0 1px 4px rgba(170,59,255,0.06)',
  },
  error: {
    bg: '#fff2f0',
    border: '1px solid #ffccc7',
  },
}

// 注入全局 keyframes（仅一次）
let keyframesInjected = false
function injectKeyframes() {
  if (keyframesInjected || typeof document === 'undefined') return
  const style = document.createElement('style')
  style.textContent = `
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulseDot {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
      40%           { transform: scale(1);   opacity: 1; }
    }
    .chat-msg-enter {
      animation: fadeInUp 0.3s ease-out;
    }
  `
  document.head.appendChild(style)
  keyframesInjected = true
}

/**
 * 消息气泡样式
 */
function getBubbleStyle(role, error) {
  if (error) return { ...BUBBLE_STYLE.assistant, ...BUBBLE_STYLE.error }
  return BUBBLE_STYLE[role] || BUBBLE_STYLE.assistant
}

/**
 * 通用对话组件
 *
 * 消息列表 + 输入框 + 流式显示。
 *
 * @param {Object} props
 * @param {Array}  props.messages    - 消息列表 [{id, role:'user'|'assistant', content, error?}]
 * @param {boolean} props.isLoading   - 是否正在生成
 * @param {Function} props.onSend    - (content: string) => void
 * @param {Function} props.onAbort   - () => void 停止生成
 * @param {string}   props.placeholder - 输入框占位文字
 * @param {boolean}  props.showEmpty  - 无消息时是否显示空状态
 * @param {string}   props.emptyText  - 空状态提示
 */
export default function ChatBox({
  messages = MOCK_MESSAGES,
  isLoading = false,
  onSend,
  onAbort,
  placeholder = '输入你的问题...',
  showEmpty = true,
  emptyText = '开始一段对话吧',
}) {
  const listRef = useRef(null)
  const inputRef = useRef(null)
  const [inputValue, setInputValue] = useState('')
  const [showScrollBtn, setShowScrollBtn] = useState(false)

  // 注入动画
  useEffect(() => { injectKeyframes() }, [])

  // 判断是否在底部（阈值 80px）
  const isNearBottom = useCallback(() => {
    const el = listRef.current
    if (!el) return true
    return el.scrollHeight - el.scrollTop - el.clientHeight < 80
  }, [])

  // 滚动到底部
  const scrollToBottom = useCallback((smooth = false) => {
    const el = listRef.current
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'instant' })
  }, [])

  // 新消息 / 流式内容变化时自动滚底（仅在用户已在底部时）
  useEffect(() => {
    if (isNearBottom()) {
      scrollToBottom(false)
    }
  }, [messages, isNearBottom, scrollToBottom])

  // 监听滚动位置，控制"回到底部"按钮
  useEffect(() => {
    const el = listRef.current
    if (!el) return
    const handleScroll = () => {
      setShowScrollBtn(!isNearBottom())
    }
    el.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()
    return () => el.removeEventListener('scroll', handleScroll)
  }, [isNearBottom])

  // 发送
  const handleSend = useCallback(() => {
    const text = inputValue.trim()
    if (!text || isLoading) return
    onSend?.(text)
    setInputValue('')
    // 发送后强制滚底
    setTimeout(() => scrollToBottom(false), 50)
  }, [inputValue, isLoading, onSend, scrollToBottom])

  // 键盘
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  // 是否显示流式加载指示器
  const showStreaming = useMemo(
    () =>
      isLoading &&
      messages.length > 0 &&
      messages[messages.length - 1]?.role === 'assistant' &&
      !messages[messages.length - 1]?.content,
    [isLoading, messages],
  )

  // ========== 渲染 ==========
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
      {/* ========== 消息列表 ========== */}
      <div
        ref={listRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px 4px 16px 0',
          minHeight: 0,
          scrollBehavior: 'smooth',
        }}
      >
        {messages.length === 0 && showEmpty ? (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
              minHeight: 200,
            }}
          >
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Text style={{ color: 'var(--text, #6b6375)', fontSize: 14 }}>
                  {emptyText}
                </Text>
              }
            />
          </div>
        ) : (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {messages.map((msg) => {
              const bubble = getBubbleStyle(msg.role, msg.error)
              return (
                <div
                  key={msg.id}
                  className="chat-msg-enter"
                  style={{
                    display: 'flex',
                    gap: 12,
                    flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                    animationDelay: '0ms',
                  }}
                >
                  {/* 头像 */}
                  <Tooltip title={msg.role === 'user' ? '你' : '学习助手'} placement="top">
                    <Avatar
                      size="small"
                      icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                      style={{
                        backgroundColor: bubble.avatarBg,
                        flexShrink: 0,
                        boxShadow: bubble.avatarShadow,
                      }}
                    />
                  </Tooltip>

                  {/* 气泡 */}
                  <div
                    style={{
                      maxWidth: '80%',
                      padding: '10px 16px',
                      borderRadius: 12,
                      textAlign: 'left',
                      backgroundColor: bubble.bg,
                      border: bubble.border,
                      boxShadow: bubble.bubbleShadow || 'none',
                      wordBreak: 'break-word',
                    }}
                  >
                    {msg.role === 'assistant' ? (
                      msg.error ? (
                        <div>
                          <Text type="danger" style={{ fontSize: 13 }}>
                            ⚠️ {msg.error}
                          </Text>
                          {msg.content && (
                            <div style={{ marginTop: 8, opacity: 0.6 }}>
                              <MarkdownRenderer content={msg.content} compact />
                            </div>
                          )}
                        </div>
                      ) : (
                        <MarkdownRenderer content={msg.content} compact />
                      )
                    ) : (
                      <Text style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</Text>
                    )}
                  </div>
                </div>
              )
            })}

            {/* 流式加载指示器 */}
            {showStreaming && (
              <div
                className="chat-msg-enter"
                style={{ paddingLeft: 44, display: 'flex', alignItems: 'center', gap: 8 }}
              >
                <ThinkingDots />
                <Text type="secondary" style={{ fontSize: 13 }}>思考中...</Text>
              </div>
            )}

            {/* 加载中（非流式） */}
            {isLoading && !showStreaming && (
              <div style={{ paddingLeft: 40, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Spin size="small" />
                <Text type="secondary" style={{ fontSize: 13 }}>生成中...</Text>
              </div>
            )}
          </Space>
        )}
      </div>

      {/* ========== 回到底部按钮 ========== */}
      {showScrollBtn && (
        <div
          style={{
            position: 'absolute',
            bottom: 70,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 10,
          }}
        >
          <Button
            shape="circle"
            size="small"
            icon={<DownOutlined />}
            onClick={() => scrollToBottom(true)}
            style={{
              boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
              opacity: 0.85,
            }}
          />
        </div>
      )}

      {/* ========== 输入区域 ========== */}
      <div
        style={{
          borderTop: '1px solid var(--border, #f0f0f0)',
          padding: '12px 0 0',
          flexShrink: 0,
        }}
      >
        <Space.Compact style={{ width: '100%' }}>
          <Input.TextArea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={isLoading}
            style={{
              borderRadius: '8px 0 0 8px',
            }}
          />
          {isLoading ? (
            <Button
              danger
              icon={<StopOutlined />}
              onClick={onAbort}
              title="停止生成"
              style={{ borderRadius: '0 8px 8px 0' }}
            />
          ) : (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!inputValue.trim()}
              style={{
                borderRadius: '0 8px 8px 0',
                background: inputValue.trim()
                  ? 'linear-gradient(135deg, #aa3bff 0%, #6366f1 100%)'
                  : undefined,
                borderColor: inputValue.trim() ? 'transparent' : undefined,
              }}
            />
          )}
        </Space.Compact>
      </div>
    </div>
  )
}

// ========== 思考中动画（三点脉冲） ==========
function ThinkingDots() {
  return (
    <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            display: 'inline-block',
            width: 6,
            height: 6,
            borderRadius: '50%',
            backgroundColor: 'var(--accent, #aa3bff)',
            animation: `pulseDot 1.2s ${i * 0.2}s infinite ease-in-out`,
          }}
        />
      ))}
    </span>
  )
}
