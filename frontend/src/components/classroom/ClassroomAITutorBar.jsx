import { useState } from 'react'
import { Avatar, Button, Input, Space, Typography, Tag } from 'antd'
import {
  RobotOutlined,
  SendOutlined,
  BulbOutlined,
  ExperimentOutlined,
  RetweetOutlined,
  LinkOutlined,
  FormOutlined,
  UpOutlined,
  DownOutlined,
} from '@ant-design/icons'

const { Text } = Typography
const { TextArea } = Input

const QUICK_ACTIONS = [
  { key: 'explain', icon: <BulbOutlined />, label: '解释这一页' },
  { key: 'example', icon: <ExperimentOutlined />, label: '举一个例子' },
  { key: 'rephrase', icon: <RetweetOutlined />, label: '换一种方式讲' },
  { key: 'connect', icon: <LinkOutlined />, label: '联系前置知识' },
  { key: 'quiz', icon: <FormOutlined />, label: '生成一道随堂题' },
]

export default function ClassroomAITutorBar({
  currentScene,
  messages,
  loading,
  onAsk,
  expanded,
  onToggleExpand,
}) {
  const [inputValue, setInputValue] = useState('')

  const handleSend = () => {
    const text = inputValue.trim()
    if (!text || loading) return
    onAsk(text)
    setInputValue('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const sceneTitle = currentScene?.title || '当前内容'
  const knowledgePoint = currentScene?.content?.knowledge_point || sceneTitle

  return (
    <div
      className="classroom-tutor-bar"
      style={{
        height: expanded ? 360 : 72,
        flexShrink: 0,
        background: 'rgba(255,255,255,0.9)',
        backdropFilter: 'blur(16px)',
        borderTop: '1px solid rgba(0,0,0,0.06)',
        transition: 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        zIndex: 40,
      }}
    >
      {/* Collapsed bar */}
      {!expanded && (
        <div
          style={{
            height: 72,
            display: 'flex',
            alignItems: 'center',
            padding: '0 20px',
            gap: 12,
            cursor: 'pointer',
          }}
          onClick={onToggleExpand}
        >
          {/* AI Avatar */}
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #6C5CE7, #8B7CF7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              boxShadow: '0 2px 12px rgba(108,92,231,0.25)',
            }}
          >
            <RobotOutlined style={{ fontSize: 20, color: '#fff' }} />
          </div>

          {/* Current context */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <Text style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>
              AI 导师讲解
            </Text>
            <Text
              type="secondary"
              style={{ fontSize: 12, marginLeft: 8, display: 'inline' }}
              ellipsis
            >
              当前：{knowledgePoint}
            </Text>
          </div>

          {/* Quick action chips (collapsed) */}
          <Space size={6}>
            {QUICK_ACTIONS.slice(0, 3).map((action) => (
              <Button
                key={action.key}
                size="small"
                icon={action.icon}
                onClick={(e) => {
                  e.stopPropagation()
                  onAsk(action.label)
                }}
                style={{
                  borderRadius: 20,
                  fontSize: 12,
                  border: '1px solid rgba(108,92,231,0.15)',
                  color: '#6C5CE7',
                  height: 32,
                  padding: '0 14px',
                }}
              >
                {action.label}
              </Button>
            ))}
          </Space>

          {/* Expand button */}
          <Button
            type="text"
            size="small"
            icon={<UpOutlined />}
            style={{ color: '#9CA3AF', flexShrink: 0 }}
          />
        </div>
      )}

      {/* Expanded chat area */}
      {expanded && (
        <>
          {/* Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 20px',
              borderBottom: '1px solid rgba(0,0,0,0.04)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #6C5CE7, #8B7CF7)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <RobotOutlined style={{ fontSize: 16, color: '#fff' }} />
              </div>
              <Text strong style={{ fontSize: 14, color: '#111827' }}>AI 导师</Text>
              <Tag color="purple" style={{ borderRadius: 8, fontSize: 11 }}>DeepSeek</Tag>
            </div>
            <Button
              type="text"
              size="small"
              icon={<DownOutlined />}
              onClick={onToggleExpand}
              style={{ color: '#9CA3AF' }}
            />
          </div>

          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflow: 'auto',
              padding: '12px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
            }}
          >
            {(!messages || messages.length === 0) && (
              <div style={{ textAlign: 'center', padding: 20 }}>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  👋 我是你的 AI 导师，点击下方快捷按钮或直接输入问题
                </Text>
              </div>
            )}
            {messages?.map((msg, i) => (
              <div
                key={i}
                style={{
                  padding: '10px 14px',
                  borderRadius: 12,
                  background: msg.role === 'user'
                    ? 'linear-gradient(135deg, #6C5CE7, #8B7CF7)'
                    : 'rgba(0,0,0,0.03)',
                  color: msg.role === 'user' ? '#fff' : '#374151',
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '75%',
                  fontSize: 13,
                  lineHeight: 1.6,
                }}
              >
                {msg.content || msg.text}
              </div>
            ))}
            {loading && (
              <div style={{ alignSelf: 'flex-start', padding: '10px 14px', color: '#9CA3AF', fontSize: 13 }}>
                <span className="gen-dot" style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: '#6C5CE7', marginRight: 6, animation: 'gen-pulse 1.2s ease-in-out infinite' }} />
                AI 思考中…
              </div>
            )}
          </div>

          {/* Quick actions + input */}
          <div style={{ padding: '12px 20px', borderTop: '1px solid rgba(0,0,0,0.04)' }}>
            {/* Quick actions */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
              {QUICK_ACTIONS.map((action) => (
                <Button
                  key={action.key}
                  size="small"
                  icon={action.icon}
                  onClick={() => {
                    onAsk(action.label)
                    if (action.key === 'quiz') {
                      setInputValue('请生成一道随堂题')
                    }
                  }}
                  style={{
                    borderRadius: 20,
                    fontSize: 12,
                    border: '1px solid rgba(108,92,231,0.12)',
                    color: '#6C5CE7',
                    height: 30,
                    padding: '0 12px',
                  }}
                >
                  {action.label}
                </Button>
              ))}
            </div>

            {/* Input row */}
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
              <TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="向 AI 导师提问…"
                autoSize={{ minRows: 1, maxRows: 3 }}
                style={{
                  flex: 1,
                  borderRadius: 12,
                  border: '1px solid rgba(0,0,0,0.1)',
                  fontSize: 13,
                  resize: 'none',
                }}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSend}
                loading={loading}
                disabled={!inputValue.trim()}
                style={{
                  borderRadius: 12,
                  background: 'linear-gradient(135deg, #6C5CE7, #8B7CF7)',
                  border: 'none',
                  height: 38,
                  width: 38,
                  flexShrink: 0,
                }}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
