import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Typography, Space } from 'antd'
import {
  RobotOutlined,
  FileTextOutlined,
  RiseOutlined,
} from '@ant-design/icons'
import ChatBox from '../components/ChatBox'
import { useChat } from '../hooks/useChat'
import { chatWithProfileStream } from '../api/profile'

const { Title, Text } = Typography

const SUGGESTIONS = [
  '帮我分析一下我的学习情况',
  '我的数学比较薄弱，怎么提升？',
  '推荐适合我的学习资源',
  '制定一个学习计划',
]

export default function ProfilePage() {
  const navigate = useNavigate()

  const streamFetcher = useCallback(
    (message, signal) => chatWithProfileStream('demo-student-01', message),
    [],
  )

  const { messages, isLoading, sendMessage, abort } = useChat({
    streamFetcher,
    initialMessages: [
      {
        id: 'welcome',
        role: 'assistant',
        content:
          '你好！我是你的专属学习助手 🤖\n\n让我们来聊聊你的学习情况吧：\n- 你的年级和目标？\n- 你擅长或不擅长的科目？\n- 你更喜欢的学习方式（看视频📺、读书📖、做题✏️）？\n\n告诉我这些，我会为你定制最佳学习路径！',
      },
    ],
  })

  const handleSuggestion = useCallback((text) => {
    sendMessage(text)
  }, [sendMessage])

  return (
    <div className="chat-full-page">
      {/* 顶部标题 + 快捷导航 */}
      <div className="chat-page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Space align="center" size={10}>
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(139,92,246,0.3)',
            }}>
              <RobotOutlined style={{ fontSize: 21, color: '#fff' }} />
            </div>
            <div>
              <Title level={4} style={{ margin: 0 }}>学习助手</Title>
              <Text type="secondary" style={{ fontSize: 13 }}>AI 驱动的个性化学习对话</Text>
            </div>
          </Space>

          {/* 快捷入口 */}
          <Space size={8}>
            <div className="chat-quick-link" onClick={() => navigate('/learning-path')}>
              <RiseOutlined style={{ fontSize: 16, color: '#8b5cf6' }} />
              <span>学习路径</span>
            </div>
            <div className="chat-quick-link" onClick={() => navigate('/resources')}>
              <FileTextOutlined style={{ fontSize: 16, color: '#1677ff' }} />
              <span>学习资源</span>
            </div>
          </Space>
        </div>
      </div>

      {/* 聊天区 */}
      <div className="chat-page-body">
        <ChatBox
          messages={messages}
          isLoading={isLoading}
          onSend={sendMessage}
          onAbort={abort}
          placeholder="说说你的学习情况，我会为你定制学习方案..."
          emptyText="和 AI 助手聊聊你的学习情况，获取个性化学习建议"
          suggestions={SUGGESTIONS}
          onSuggestionClick={handleSuggestion}
        />
      </div>
    </div>
  )
}
