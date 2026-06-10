import { useState, useCallback } from 'react'
import { Row, Col, Typography, Divider } from 'antd'
import ChatBox from '../components/ChatBox'
import ProfileCard from '../components/ProfileCard'
import { useChat } from '../hooks/useChat'
import { chatWithProfileStream } from '../api/profile'

const { Title } = Typography

/**
 * 学生画像页 — 对话式画像采集 + 画像卡片展示
 */
export default function ProfilePage() {
  const [profile, setProfile] = useState(null)

  const studentId = 'demo-student-01'

  // 流式对话 fetcher
  const streamFetcher = useCallback(
    (message, signal) => chatWithProfileStream(studentId, message),
    [studentId],
  )

  const { messages, isLoading, sendMessage, abort } = useChat({
    streamFetcher,
    initialMessages: [
      {
        id: 'welcome',
        role: 'assistant',
        content:
          '你好！我是你的学习助手。让我们先了解一下你的学习情况吧。\n\n你可以告诉我：\n- 你的年级和学科偏好\n- 你擅长和不擅长的科目\n- 你的学习目标和时间安排\n- 你更喜欢的学习方式（看视频、读书、做题等）',
      },
    ],
  })

  // 当对话完成一轮后更新画像（简化处理：提取最后一条 assistant 消息）
  const handleSend = useCallback(
    async (content) => {
      await sendMessage(content)
      // 这里可以从后端获取更新的画像
      // const updated = await getProfile(studentId)
      // setProfile(updated)
    },
    [sendMessage],
  )

  return (
    <div>
      <Title level={3}>学生画像</Title>

      <Row gutter={[24, 24]}>
        {/* 左侧：对话区 */}
        <Col xs={24} lg={14}>
          <div style={{ height: '60vh', border: '1px solid #f0f0f0', borderRadius: 8, padding: '0 16px' }}>
            <ChatBox
              messages={messages}
              isLoading={isLoading}
              onSend={handleSend}
              onAbort={abort}
              placeholder="描述你的学习情况..."
              emptyText="和助手聊聊你的学习情况吧"
            />
          </div>
        </Col>

        {/* 右侧：画像卡片 */}
        <Col xs={24} lg={10}>
          <ProfileCard profile={profile} loading={isLoading} />
        </Col>
      </Row>
    </div>
  )
}
