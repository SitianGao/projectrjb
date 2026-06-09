import { useState, useCallback, useEffect } from 'react'
import { Row, Col, Typography, Button, Card, List, Tag, Space, Empty, Modal, Input } from 'antd'
import { PlusOutlined, MessageOutlined, DeleteOutlined } from '@ant-design/icons'
import ChatBox from '../components/ChatBox'
import { useChat } from '../hooks/useChat'
import { askTutorStream, getTutorSessions, createTutorSession } from '../api/tutor'
import { formatRelativeTime } from '../utils/format'

const { Title, Text } = Typography

/**
 * 智能辅导页 — 问答聊天 + 会话管理
 */
export default function TutorPage() {
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [newSessionModal, setNewSessionModal] = useState(false)
  const [newSessionTitle, setNewSessionTitle] = useState('')

  const studentId = 'demo-student-01'

  // 流式辅导对话
  const streamFetcher = useCallback(
    (message, signal) =>
      askTutorStream({
        student_id: studentId,
        session_id: activeSessionId,
        message,
      }),
    [studentId, activeSessionId],
  )

  const { messages, isLoading, sendMessage, abort, setMessages } = useChat({
    streamFetcher,
    initialMessages: [
      {
        id: 'tutor-welcome',
        role: 'assistant',
        content:
          '你好！我是你的专属辅导老师。你可以问我任何学习上的问题：\n\n📖 **解题答疑** — 不会做的题目随时问我\n📝 **知识点讲解** — 帮你理解难懂的概念\n🎯 **练习推荐** — 根据你的薄弱点推荐题目\n💡 **学习建议** — 给你高效的学习方法指导\n\n告诉我你今天想学什么？',
      },
    ],
  })

  useEffect(() => {
    loadSessions()
  }, [])

  async function loadSessions() {
    setLoadingSessions(true)
    try {
      const data = await getTutorSessions(studentId)
      setSessions(Array.isArray(data) ? data : data?.sessions || [])
    } catch {
      setSessions([
        { id: 's1', title: '二次函数答疑', updatedAt: new Date(), messageCount: 12 },
        { id: 's2', title: '英语语法解惑', updatedAt: new Date(Date.now() - 86400000), messageCount: 8 },
      ])
    } finally {
      setLoadingSessions(false)
    }
  }

  async function handleNewSession() {
    if (!newSessionTitle.trim()) return
    try {
      const data = await createTutorSession({ student_id: studentId, title: newSessionTitle })
      setActiveSessionId(data?.id || data?.session_id)
      setNewSessionModal(false)
      setNewSessionTitle('')
      loadSessions()
      setMessages([
        {
          id: 'tutor-new',
          role: 'assistant',
          content: `新会话"${newSessionTitle}"已创建！请告诉我你想讨论什么问题？`,
        },
      ])
    } catch {
      setNewSessionModal(false)
      setNewSessionTitle('')
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0 }}>智能辅导</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setNewSessionModal(true)}>
          新建会话
        </Button>
      </div>

      <Row gutter={[24, 24]} style={{ marginTop: 16 }}>
        {/* 左侧：会话列表 */}
        <Col xs={24} md={6}>
          <Card
            title="辅导会话"
            size="small"
            loading={loadingSessions}
            style={{ height: '60vh', overflowY: 'auto' }}
          >
            {sessions.length === 0 ? (
              <Empty description="暂无会话" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
              <List
                dataSource={sessions}
                renderItem={(s) => (
                  <List.Item
                    style={{
                      cursor: 'pointer',
                      background: s.id === activeSessionId ? '#e6f4ff' : 'transparent',
                      padding: '8px',
                      borderRadius: 6,
                    }}
                    onClick={() => setActiveSessionId(s.id)}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <MessageOutlined />
                          <Text>{s.title}</Text>
                        </Space>
                      }
                      description={
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {s.messageCount || 0} 条消息 · {formatRelativeTime(s.updatedAt)}
                        </Text>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>

        {/* 右侧：聊天区 */}
        <Col xs={24} md={18}>
          <div
            style={{
              height: '60vh',
              border: '1px solid #f0f0f0',
              borderRadius: 8,
              padding: '0 16px',
            }}
          >
            <ChatBox
              messages={messages}
              isLoading={isLoading}
              onSend={sendMessage}
              onAbort={abort}
              placeholder={activeSessionId ? '输入你的问题...' : '请先选择或创建一个会话'}
              showEmpty={false}
            />
          </div>
        </Col>
      </Row>

      {/* 新建会话弹窗 */}
      <Modal
        title="新建辅导会话"
        open={newSessionModal}
        onOk={handleNewSession}
        onCancel={() => setNewSessionModal(false)}
        okText="创建"
        cancelText="取消"
      >
        <Input
          placeholder="输入会话标题（如：二次函数答疑）"
          value={newSessionTitle}
          onChange={(e) => setNewSessionTitle(e.target.value)}
          onPressEnter={handleNewSession}
        />
      </Modal>
    </div>
  )
}
