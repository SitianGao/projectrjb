import { useState, useCallback, useMemo } from 'react'
import { Row, Col, Typography, Card, Tag, Avatar, Space } from 'antd'
import {
  IdcardOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import ChatBox from '../components/ChatBox'
import ProfileCard from '../components/ProfileCard'
import { useChat } from '../hooks/useChat'
import { chatWithProfileStream } from '../api/profile'

const { Title, Text } = Typography

// ========== 画像完成度权重 ==========
const COMPLETION_WEIGHTS = {
  name: 30,
  strengths: 25,
  weaknesses: 20,
  topics: 15,
  style: 10,
}
const COMPLETION_MAX = Object.values(COMPLETION_WEIGHTS).reduce((a, b) => a + b, 0) // 100

// ========== 横幅样式 ==========
const BANNER_WRAPPER_STYLE = {
  position: 'relative',
  borderRadius: 16,
  padding: '24px 32px',
  marginBottom: 24,
  background: 'linear-gradient(135deg, #0f0c29 0%, #1a1040 40%, #0d1b3e 100%)',
  overflow: 'hidden',
  color: '#fff',
  boxShadow: '0 4px 32px rgba(99, 102, 241, 0.25), 0 1px 4px rgba(0, 0, 0, 0.15)',
}

const BANNER_GLOW_TOP_STYLE = {
  position: 'absolute',
  top: -30,
  right: -30,
  width: 200,
  height: 200,
  borderRadius: '50%',
  background: 'radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, rgba(99, 102, 241, 0.1) 40%, transparent 70%)',
  pointerEvents: 'none',
}

const BANNER_GLOW_BOTTOM_STYLE = {
  position: 'absolute',
  bottom: -40,
  left: '15%',
  width: 260,
  height: 130,
  borderRadius: '50%',
  background: 'radial-gradient(ellipse, rgba(59, 130, 246, 0.2) 0%, rgba(99, 102, 241, 0.08) 40%, transparent 70%)',
  pointerEvents: 'none',
}

const BANNER_GRID_STYLE = {
  position: 'absolute',
  inset: 0,
  backgroundImage:
    'linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)',
  backgroundSize: '40px 40px',
  pointerEvents: 'none',
}

// ========== 卡片通用样式 ==========
const CARD_STYLE = {
  borderRadius: 12,
  border: '1px solid var(--border, #e5e4e7)',
  background: 'rgba(255,255,255,0.8)',
  backdropFilter: 'blur(8px)',
  boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)',
}

const ICON_WRAP_STYLE = (size = 32, radius = 8) => ({
  width: size,
  height: size,
  borderRadius: radius,
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: Math.round(size * 0.47),
  color: '#fff',
  background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
  boxShadow: '0 4px 14px rgba(139, 92, 246, 0.3)',
})

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

  // 当对话完成一轮后更新画像
  const handleSend = useCallback(
    async (content) => {
      await sendMessage(content)
      // TODO: 从后端获取更新后的画像
      // const updated = await getProfile(studentId)
      // setProfile(updated)
    },
    [sendMessage],
  )

  /** 画像完成度：按已填字段加权计算（最大 100%） */
  const completionPercent = useMemo(() => {
    if (!profile) return 0
    const score =
      (profile.name ? COMPLETION_WEIGHTS.name : 0) +
      (profile.strengths?.length ? COMPLETION_WEIGHTS.strengths : 0) +
      (profile.weaknesses?.length ? COMPLETION_WEIGHTS.weaknesses : 0) +
      (profile.topics?.length ? COMPLETION_WEIGHTS.topics : 0) +
      (profile.style ? COMPLETION_WEIGHTS.style : 0)
    return Math.min(100, Math.round((score / COMPLETION_MAX) * 100))
  }, [profile])

  return (
    <div>
      <Title level={3} style={{ color: '#1a1a2e', marginTop: -8, marginBottom: 12 }}>
        学生画像
      </Title>

      {/* ========== 引导横幅 ========== */}
      <div style={BANNER_WRAPPER_STYLE}>
        {/* 光晕装饰 */}
        <div style={BANNER_GLOW_TOP_STYLE} />
        <div style={BANNER_GLOW_BOTTOM_STYLE} />
        {/* 网格 */}
        <div style={BANNER_GRID_STYLE} />

        <Row align="middle" gutter={[16, 12]} style={{ position: 'relative', zIndex: 1 }}>
          <Col>
            <Avatar
              size={48}
              icon={<IdcardOutlined />}
              style={{
                backgroundColor: 'transparent',
                border: '2px solid rgba(139, 92, 246, 0.6)',
                boxShadow: '0 0 24px rgba(139, 92, 246, 0.35), inset 0 0 12px rgba(139, 92, 246, 0.1)',
              }}
            />
          </Col>
          <Col flex="auto">
            <Text
              strong
              style={{
                color: '#fff',
                fontSize: 20,
                lineHeight: 1.4,
              }}
            >
              快来完善你的学习画像，以获得更精准的学习推荐吧
            </Text>
            <br />
            <Text style={{ color: 'rgba(255,255,255,0.72)', fontSize: 13 }}>
              与助手对话，告诉我们你的学习情况（信息越完善，推荐越精准哦）
            </Text>
          </Col>
          {completionPercent > 0 && (
            <Col>
              <Tag
                color="purple"
                style={{
                  borderRadius: 6,
                  background: 'rgba(139, 92, 246, 0.25)',
                  border: '1px solid rgba(139, 92, 246, 0.45)',
                  color: '#c4b5fd',
                  fontSize: 13,
                  padding: '2px 12px',
                  transition: 'all 0.3s ease',
                  fontWeight: 500,
                }}
              >
                画像完成度 {completionPercent}%
              </Tag>
            </Col>
          )}
        </Row>
      </div>

      {/* ========== 双栏布局 ========== */}
      <Row gutter={[24, 24]}>
        {/* 左侧：对话区 */}
        <Col xs={24} lg={13}>
          <Card
            title={
              <Space>
                <div style={ICON_WRAP_STYLE(32, 8)}>
                  <MessageOutlined />
                </div>
                <span style={{ color: '#1a1a2e', fontWeight: 600 }}>
                  学习助手
                </span>
              </Space>
            }
            style={CARD_STYLE}
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
        <Col xs={24} lg={11}>
          <ProfileCard profile={profile} loading={isLoading} />
        </Col>
      </Row>
    </div>
  )
}
