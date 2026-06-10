import { useState, useCallback, useEffect, useRef } from 'react'
import { Row, Col, Typography, Select, Button, Space, Divider, Tag } from 'antd'
import { ExperimentOutlined, ReloadOutlined } from '@ant-design/icons'
import ChatBox from '../components/ChatBox'
import ProfileCard from '../components/ProfileCard'
import { useChat } from '../hooks/useChat'
import { chatWithProfileStream, getProfile, getTestCases } from '../api/profile'

const { Title, Text } = Typography

/**
 * 学生画像页 —— 对话式画像采集 + 画像卡片展示 + 测试用例演示
 */
export default function ProfilePage() {
  const [profile, setProfile] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)
  const [testCases, setTestCases] = useState([])
  const [activeTestCase, setActiveTestCase] = useState(null)
  const pollingRef = useRef(null)

  const studentId = 'demo-student-01'

  // ---- 拉取最新画像 ----
  const fetchProfile = useCallback(async () => {
    try {
      setProfileLoading(true)
      const data = await getProfile(studentId)
      if (data && data.profile) {
        setProfile(data)
        setActiveTestCase(null) // 清除测试用例标记
      }
    } catch (err) {
      if (err?.response?.status !== 404 && err?.status !== 404) {
        console.warn('获取画像失败:', err)
      }
    } finally {
      setProfileLoading(false)
    }
  }, [studentId])

  // ---- 加载测试用例 ----
  const loadTestCases = useCallback(async () => {
    try {
      const res = await getTestCases()
      if (res?.data) {
        setTestCases(res.data)
      }
    } catch (err) {
      console.warn('加载测试用例失败:', err)
    }
  }, [])

  // 首次加载
  useEffect(() => {
    fetchProfile()
    loadTestCases()
  }, [fetchProfile, loadTestCases])

  // 选择一个测试用例 → 直接显示其画像
  const handleSelectTestCase = useCallback(
    (caseIdx) => {
      if (caseIdx === undefined || caseIdx === null) {
        setProfile(null)
        setActiveTestCase(null)
        fetchProfile()
        return
      }
      const tc = testCases[caseIdx]
      if (tc?.final_profile) {
        setProfile(tc.final_profile)
        setActiveTestCase(tc)
      }
    },
    [testCases, fetchProfile],
  )

  // ---- 流式对话 ----
  const streamFetcher = useCallback(
    (msg, signal) => chatWithProfileStream(studentId, msg, signal),
    [studentId],
  )

  const { messages, isLoading, sendMessage, abort } = useChat({
    streamFetcher,
    initialMessages: [
      {
        id: 'welcome',
        role: 'assistant',
        content:
          '你好！我是你的学习助手。让我们先了解一下你的学习情况吧。\n\n你可以告诉我：\n- 你的年级和专业背景\n- 你擅长和不擅长的科目\n- 你的学习目标和时间安排\n- 你更喜欢的学习方式（看视频、读书、做题等）',
      },
    ],
  })

  // 发送消息 → 等待流式回复 → 拉取画像
  const handleSend = useCallback(
    async (content) => {
      await sendMessage(content)
      if (pollingRef.current) clearTimeout(pollingRef.current)
      pollingRef.current = setTimeout(async () => {
        await fetchProfile()
        pollingRef.current = null
      }, 800)
    },
    [sendMessage, fetchProfile],
  )

  // 清理
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearTimeout(pollingRef.current)
    }
  }, [])

  // ---- 渲染 ----
  const testCaseOptions = testCases.map((tc, i) => ({
    value: i,
    label: tc.case || `案例 ${i + 1}`,
  }))

  return (
    <div>
      {/* 标题栏 + 测试用例选择器 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={3} style={{ margin: 0 }}>学生画像</Title>
        </Col>
        <Col>
          <Space>
            <Select
              placeholder="📋 选择测试案例（3组典型画像）"
              style={{ minWidth: 360 }}
              value={activeTestCase ? testCases.indexOf(activeTestCase) : undefined}
              onChange={handleSelectTestCase}
              options={testCaseOptions}
              allowClear
              onClear={() => handleSelectTestCase(null)}
              notFoundContent="加载测试用例中..."
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchProfile}
              loading={profileLoading}
            >
              刷新
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 测试用例描述 */}
      {activeTestCase && (
        <div
          style={{
            background: '#e6f4ff',
            borderRadius: 8,
            padding: '10px 16px',
            marginBottom: 16,
            border: '1px solid #91caff',
          }}
        >
          <Space>
            <ExperimentOutlined style={{ color: '#1677ff' }} />
            <Text strong>{activeTestCase.case}</Text>
            <Tag color="blue">{activeTestCase.rounds} 轮对话</Tag>
            <Tag color="green">
              完整度 {(activeTestCase.final_profile?.completeness * 100).toFixed(0)}%
            </Tag>
            <Tag color="orange">
              置信度 {(activeTestCase.final_profile?.confidence * 100).toFixed(0)}%
            </Tag>
          </Space>
        </div>
      )}

      <Row gutter={[24, 24]}>
        {/* 左侧：对话区（测试用例模式下提示） */}
        <Col xs={24} lg={14}>
          <div
            style={{
              height: '60vh',
              border: '1px solid #f0f0f0',
              borderRadius: 8,
              padding: '0 16px',
              background: '#fff',
            }}
          >
            {activeTestCase ? (
              <div style={{ padding: 24 }}>
                <Title level={5}>对话记录（{activeTestCase.rounds} 轮）</Title>
                {activeTestCase.final_profile?.profile?.learning_history?.map((msg, i) => (
                  <div
                    key={i}
                    style={{
                      marginBottom: 12,
                      padding: '10px 14px',
                      borderRadius: 8,
                      background: i % 2 === 0 ? '#e6f4ff' : '#f5f5f5',
                    }}
                  >
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {i % 2 === 0 ? '👤 学生' : '🤖 助手'} · 第 {Math.floor(i / 2) + 1} 轮
                    </Text>
                    <Text style={{ display: 'block', marginTop: 4 }}>{msg}</Text>
                  </div>
                ))}
                <Divider />
                <Text type="secondary">
                  💡 这是一个测试案例的对话记录。切换到左侧输入框可以开始你的真实对话。
                </Text>
              </div>
            ) : (
              <ChatBox
                messages={messages}
                isLoading={isLoading}
                onSend={handleSend}
                onAbort={abort}
                placeholder="描述你的学习情况，比如：我是大二CS专业，学过Python，数学偏弱，想学ML..."
                emptyText="和助手聊聊你的学习情况吧"
              />
            )}
          </div>
        </Col>

        {/* 右侧：画像卡片 */}
        <Col xs={24} lg={10}>
          <ProfileCard profile={profile} loading={profileLoading} />
        </Col>
      </Row>
    </div>
  )
}
