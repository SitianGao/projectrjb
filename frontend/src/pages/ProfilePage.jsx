import { useState, useCallback } from 'react'
import { Row, Col, Typography, Card, Tag, Avatar, Space } from 'antd'
import {
  UserOutlined,
  InfoCircleOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import ChatBox from '../components/ChatBox'
import ProfileCard from '../components/ProfileCard'
import { useChat } from '../hooks/useChat'
import { chatWithProfileStream } from '../api/profile'

const { Title, Text } = Typography

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
          '你好！我是你的学习助手，让我们来聊聊你的学习情况吧。\n\n你可以告诉我：\n- 你的年级\n- 你擅长或不擅长的科目\n- 你的学习目标\n- 你喜欢的的学习方式（比如：看视频、读书、做题等）',
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

  /** 画像完成度：粗略按已填字段数估算 */
  const completionPercent = profile
    ? Math.min(
        100,
        Math.round(
          ((profile.name ? 30 : 0) +
            (profile.strengths?.length ? 25 : 0) +
            (profile.weaknesses?.length ? 20 : 0) +
            (profile.topics?.length ? 15 : 0) +
            (profile.style ? 10 : 0)) /
            1,
        ),
      )
    : 0

  return (
    <div>
      <Title level={3} style={{ color: 'var(--text-h, #08060d)', marginBottom: 24 }}>
        学生画像
      </Title>

      {/* ========== 引导横幅 — 深色科技渐变 ========== */}
      <div
        style={{
          position: 'relative',
          borderRadius: 16,
          padding: '24px 32px',
          marginBottom: 24,
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
          overflow: 'hidden',
          color: '#fff',
          boxShadow: '0 4px 24px rgba(15, 52, 96, 0.3)',
        }}
      >
        {/* 背景光晕 */}
        <div
          style={{
            position: 'absolute',
            top: -30,
            right: -30,
            width: 180,
            height: 180,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(170,59,255,0.2) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: -40,
            left: '20%',
            width: 240,
            height: 120,
            borderRadius: '50%',
            background: 'radial-gradient(ellipse, rgba(99,102,241,0.15) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />
        {/* 网格装饰 */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
            pointerEvents: 'none',
          }}
        />

        <Row align="middle" gutter={[16, 12]} style={{ position: 'relative', zIndex: 1 }}>
          <Col>
            <Avatar
              size={48}
              icon={<InfoCircleOutlined />}
              style={{
                backgroundColor: 'transparent',
                border: '2px solid rgba(170,59,255,0.5)',
                boxShadow: '0 0 18px rgba(170,59,255,0.3)',
              }}
            />
          </Col>
          <Col flex="auto">
            <Text strong style={{ color: '#fff', fontSize: 20 }}>
              快来完善你的学习画像，以获得更精准的学习推荐吧
            </Text>
            <br />
            <Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13 }}>
              与助手对话，告诉我们你的学习情况（信息越完善，推荐越精准哦）
            </Text>
          </Col>
          {completionPercent > 0 && (
            <Col>
              <Tag
                color="purple"
                style={{
                  borderRadius: 4,
                  background: 'rgba(170,59,255,0.2)',
                  border: '1px solid rgba(170,59,255,0.4)',
                  color: '#d4adfc',
                  fontSize: 13,
                }}
              >
                画像完成度 {completionPercent}%
              </Tag>
            </Col>
          )}
        </Row>
      </div>

      <Row gutter={[24, 24]}>
        {/* 左侧：对话区 */}
        <Col xs={24} lg={14}>
          <Card
            title={
              <Space>
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 8,
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 15,
                    color: '#fff',
                    background: 'linear-gradient(135deg, #aa3bff 0%, #6366f1 100%)',
                    boxShadow: '0 3px 10px rgba(170,59,255,0.25)',
                  }}
                >
                  <MessageOutlined />
                </div>
                <span style={{ color: '#2c2c2c' }}>
                  与学习助手对话
                </span>
              </Space>
            }
            style={{
              borderRadius: 12,
              border: '1px solid var(--border, #e5e4e7)',
              background: 'rgba(255,255,255,0.7)',
              backdropFilter: 'blur(6px)',
            }}
            styles={{
              body: {
                padding: '0 16px',
                height: 'calc(100% - 57px)',
                display: 'flex',
                flexDirection: 'column',
              },
            }}
            className="tech-profile-chat"
          >
            <div style={{ flex: 1, minHeight: 400, display: 'flex', flexDirection: 'column' }}>
              <ChatBox
                messages={messages}
                isLoading={isLoading}
                onSend={handleSend}
                onAbort={abort}
                placeholder="描述你的学习情况..."
                emptyText="和助手聊聊你的学习情况吧"
              />
            </div>
          </Card>
        </Col>

        {/* 右侧：画像卡片 */}
        <Col xs={24} lg={10}>
          <ProfileCard profile={profile} loading={isLoading} />
        </Col>
      </Row>
    </div>
  )
}
