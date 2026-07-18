import { useCallback } from 'react'
import { Typography, Tag } from 'antd'
import { RobotOutlined } from '@ant-design/icons'
import ChatBox from '../components/ChatBox'
import MyCourses from '../components/MyCourses'
import { useChat } from '../hooks/useChat'
import { useAuth } from '../contexts/AuthContext'
import './HomePage.css'

const { Title, Text } = Typography

const SUGGESTIONS = [
  '帮我分析一下我的学习情况',
  '我的数学比较薄弱，怎么提升？',
  '推荐适合我的学习资源',
  '制定一个学习计划',
]

export default function HomePage() {
  const { user, studentId } = useAuth()

  const streamFetcher = useCallback(
    (msg, signal, options) => {
      const body = {
        student_id: studentId,
        message: msg,
        ...(options?.history && { history: options.history }),
        ...(options?.current_profile && { current_profile: options.current_profile }),
      }
      return fetch('/api/profile/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal,
      }).then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res
      })
    },
    [studentId],
  )

  const { messages, isLoading, sendMessage, abort } = useChat({
    streamFetcher,
    initialMessages: [{
      id: 'welcome',
      role: 'assistant',
      content: `你好！我是 ProfileAgent，你的专属学习画像分析师 🤖\n\n告诉我你的学习情况，我会为你定制最佳学习方案：\n- 你的年级和目标？\n- 你擅长或不擅长的科目？\n- 你更喜欢的学习方式？`,
    }],
  })

  const handleSuggestion = useCallback((t, opts) => sendMessage(t, opts), [sendMessage])

  return (
    <div className="chat-home-page">
      <div className="chat-home-container">
        {/* 顶部标题区 */}
        <div className="chat-home-header">
          <div className="chat-home-avatar">
            <RobotOutlined />
          </div>
          <Title level={2} className="chat-home-title">
            ProfileAgent
          </Title>
          <Text className="chat-home-subtitle">
            你好{user?.name ? `，${user.name}` : ''} 👋 让我了解你的学习情况，为你定制专属学习方案
          </Text>
          <Tag color="purple" className="chat-home-tag">AI 学习画像分析师</Tag>
        </div>

        {/* 居中聊天框 */}
        <div className="chat-home-chatbox-wrapper">
          <ChatBox
            messages={messages}
            isLoading={isLoading}
            onSend={sendMessage}
            onAbort={abort}
            placeholder="说说你的学习情况，我会为你定制学习方案..."
            emptyText="和 ProfileAgent 聊聊你的学习情况"
            suggestions={SUGGESTIONS}
            onSuggestionClick={handleSuggestion}
            showStyleSelector={false}
            headerHint="介绍一下自己，ProfileAgent 会根据你的背景生成个性化学习画像"
          />
        </div>

        {/* 下方课程入口 */}
        <div className="chat-home-courses">
          <MyCourses />
        </div>
      </div>
    </div>
  )
}
