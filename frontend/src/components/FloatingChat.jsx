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

const STYLE_PROMPTS = {
  analogy: '请用生动的生活类比和比喻来解释以下问题：',
  formula: '请用严谨的数学公式和推导步骤来解释以下问题：',
  diagram: '请用文字描述流程图或使用 mermaid 语法画图的方式来解释以下问题：',
  story: '请用一个有趣的故事或真实案例来讲解以下知识点：',
}

/**
 * 右下角悬浮对话按钮 + 抽屉式对话窗格
 */
export default function FloatingChat() {
  const [open, setOpen] = useState(false)

  const streamFetcher = useCallback(
    (message, signal, options) => {
      const style = options?.style
      const stylePrompt = STYLE_PROMPTS[style]
      const styledMsg = stylePrompt ? `${stylePrompt}\n\n${message}` : message
      return startProfileChat({ student_id: 'demo-student-01', message: styledMsg, style })
    },
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
            onSuggestionClick={(text, opts) => sendMessage(text, opts)}
          />
        </div>
      </Drawer>
    </>
  )
}
