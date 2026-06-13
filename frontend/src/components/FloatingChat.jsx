import { useState, useCallback } from 'react'
import { Button, Drawer } from 'antd'
import { MessageOutlined, CloseOutlined } from '@ant-design/icons'
import ChatBox from './ChatBox'
import { useChat } from '../hooks/useChat'
import { startProfileChat } from '../api/profile'

const SUGGESTIONS = [
  '帮我分析一下我的学习情况',
  '我的数学比较薄弱，怎么提升？',
  '推荐适合我的学习资源',
]

/**
 * 右下角悬浮对话按钮 + 抽屉式对话窗格
 */
export default function FloatingChat() {
  const [open, setOpen] = useState(false)

  const streamFetcher = useCallback(
    (message, signal) => startProfileChat({ student_id: 'demo-student-01', message }),
    [],
  )

  const { messages, isLoading, sendMessage, abort, setMessages } = useChat({
    streamFetcher,
    initialMessages: [{
      id: 'float-welcome',
      role: 'assistant',
      content: '你好！有什么可以帮你的？💬',
    }],
  })

  return (
    <>
      {/* 悬浮按钮 */}
      <div style={{
        position: 'fixed',
        bottom: 32,
        right: 32,
        zIndex: 999,
      }}>
        {open ? (
          <Button
            shape="circle"
            size="large"
            icon={<CloseOutlined />}
            onClick={() => setOpen(false)}
            style={{
              width: 52, height: 52,
              background: '#fff',
              boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
              border: '1px solid #e8e8e8',
            }}
          />
        ) : (
          <Button
            shape="circle"
            size="large"
            icon={<MessageOutlined style={{ fontSize: 22 }} />}
            onClick={() => setOpen(true)}
            style={{
              width: 56, height: 56,
              background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
              border: 'none',
              boxShadow: '0 4px 20px rgba(139,92,246,0.4)',
              color: '#fff',
              animation: 'pulse 2s infinite',
            }}
          />
        )}
      </div>

      {/* 抽屉对话窗 */}
      <Drawer
        title="学习助手"
        open={open}
        onClose={() => setOpen(false)}
        placement="right"
        width={420}
        styles={{ body: { padding: 0, height: '100%', display: 'flex', flexDirection: 'column' } }}
      >
        <div style={{ flex: 1, minHeight: 0 }}>
          <ChatBox
            messages={messages}
            isLoading={isLoading}
            onSend={sendMessage}
            onAbort={abort}
            placeholder="说说你的学习情况..."
            suggestions={SUGGESTIONS}
            onSuggestionClick={(text) => sendMessage(text)}
          />
        </div>
      </Drawer>
    </>
  )
}
