import { useRef, useEffect, useCallback, useState } from 'react'
import { Input, Button, Space, Avatar, Typography, Spin, Empty } from 'antd'
import { SendOutlined, UserOutlined, RobotOutlined, StopOutlined } from '@ant-design/icons'
import MarkdownRenderer from './MarkdownRenderer'

const { Text } = Typography

/**
 * 通用对话组件
 *
 * 消息列表 + 输入框 + 流式显示。
 *
 * @param {Object} props
 * @param {Array} props.messages - 消息列表 [{id, role:'user'|'assistant', content}]
 * @param {boolean} props.isLoading - 是否正在生成
 * @param {Function} props.onSend - (content: string) => void
 * @param {Function} props.onAbort - () => void 停止生成
 * @param {string} props.placeholder - 输入框占位文字
 * @param {boolean} props.showEmpty - 无消息时是否显示空状态
 * @param {string} props.emptyText - 空状态提示
 */
export default function ChatBox({
  messages = [],
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

  // 新消息到来时自动滚到底部
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = useCallback(() => {
    const text = inputValue.trim()
    if (!text || isLoading) return
    onSend?.(text)
    setInputValue('')
  }, [inputValue, isLoading, onSend])

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* 消息列表 */}
      <div
        ref={listRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px 0',
          minHeight: 0,
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
            <Empty description={emptyText} />
          </div>
        ) : (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  gap: 12,
                  flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                }}
              >
                <Avatar
                  size="small"
                  icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                  style={{
                    backgroundColor: msg.role === 'user' ? '#1677ff' : '#aa3bff',
                    flexShrink: 0,
                    boxShadow: msg.role === 'assistant'
                      ? '0 2px 8px rgba(170,59,255,0.3)'
                      : '0 2px 8px rgba(22,119,255,0.25)',
                  }}
                />
                <div
                  style={{
                    maxWidth: '80%',
                    padding: '10px 16px',
                    borderRadius: 12,
                    textAlign: 'left',
                    backgroundColor:
                      msg.role === 'user'
                        ? '#e6f4ff'
                        : msg.error
                          ? '#fff2f0'
                          : 'rgba(170,59,255,0.06)',
                    border: msg.error
                      ? '1px solid #ffccc7'
                      : msg.role === 'assistant'
                        ? '1px solid rgba(170,59,255,0.18)'
                        : '1px solid rgba(22,119,255,0.15)',
                    boxShadow: msg.role === 'assistant'
                      ? '0 1px 4px rgba(170,59,255,0.06)'
                      : 'none',
                  }}
                >
                  {msg.role === 'assistant' ? (
                    <MarkdownRenderer content={msg.content} compact />
                  ) : (
                    <Text>{msg.content}</Text>
                  )}
                </div>
              </div>
            ))}
            {isLoading && messages.length > 0 && !messages[messages.length - 1]?.content && (
              <div style={{ paddingLeft: 40 }}>
                <Spin size="small" /> <Text type="secondary">思考中...</Text>
              </div>
            )}
          </Space>
        )}
      </div>

      {/* 输入区域 */}
      <div
        style={{
          borderTop: '1px solid #f0f0f0',
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
          />
          {isLoading ? (
            <Button
              danger
              icon={<StopOutlined />}
              onClick={onAbort}
              title="停止生成"
            />
          ) : (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!inputValue.trim()}
            />
          )}
        </Space.Compact>
      </div>
    </div>
  )
}
