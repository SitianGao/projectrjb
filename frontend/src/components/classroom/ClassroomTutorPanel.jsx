import { useMemo, useState } from 'react'
import { Avatar, Button, Card, Input, Space, Typography } from 'antd'
import { RobotOutlined, SendOutlined, UserOutlined } from '@ant-design/icons'
import TutorQuickActions from './TutorQuickActions'
import TutorInterventionCard from './TutorInterventionCard'
import MarkdownRenderer from '../MarkdownRenderer'

const { Text, Paragraph } = Typography

/**
 * Last-resort JSON stripping: if the content looks like JSON,
 * try to extract the readable answer text from it.
 */
function stripJsonWrapper(text) {
  if (!text || typeof text !== 'string') return text
  const trimmed = text.trim()
  if (!trimmed.startsWith('{') && !trimmed.startsWith('```')) return text

  // Try 1: JSON.parse
  try {
    let jsonStr = trimmed
    const codeBlockMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)```/)
    if (codeBlockMatch) jsonStr = codeBlockMatch[1].trim()
    const start = jsonStr.indexOf('{')
    const end = jsonStr.lastIndexOf('}')
    if (start >= 0 && end > start) jsonStr = jsonStr.slice(start, end + 1)
    const parsed = JSON.parse(jsonStr)
    if (typeof parsed === 'object' && parsed !== null) {
      const keys = ['answer', 'content', 'text', 'response', 'message', 'explanation']
      for (const key of keys) {
        if (typeof parsed[key] === 'string' && parsed[key].length > 5) return parsed[key]
      }
    }
  } catch {}

  // Try 2: regex for common answer keys
  const m = trimmed.match(/"(?:answer|content|text|response|message|explanation)"\s*:\s*"((?:[^"\\]|\\.)*)"/)
  if (m && m[1] && m[1].length > 5) return m[1].replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\')

  // Try 3: longest string value
  const all = trimmed.match(/"((?:[^"\\]|\\.)*)"/g)
  if (all) {
    let best = ''
    for (const s of all) { const u = s.slice(1, -1); if (u.length > best.length && !u.startsWith('{') && !u.startsWith('[')) best = u }
    if (best.length > 10) return best.replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\')
  }

  return text
}

export default function ClassroomTutorPanel({
  currentScene,
  messages,
  loading,
  onAsk,
  intervention,
}) {
  const [input, setInput] = useState('')
  const recommendedQuestions = useMemo(() => (
    currentScene?.recommended_questions || currentScene?.content?.recommended_questions || [
      '这个知识点考试会怎么考？',
      '能不能用生活例子解释一下？',
      '我应该先记住哪一步？',
    ]
  ), [currentScene])

  const submit = (value = input) => {
    const question = String(value || '').trim()
    if (!question) return
    setInput('')
    onAsk?.(question)
  }

  return (
    <Card className="classroom-tutor" title={<Space><RobotOutlined />AI 导师</Space>}>
      <div className="tutor-knowledge">
        <Text type="secondary">当前知识点</Text>
        <Text strong>{currentScene?.knowledge_point || currentScene?.title || '梯度下降'}</Text>
      </div>

      <TutorInterventionCard intervention={intervention} />

      <div className="tutor-recommendations">
        <Text strong>推荐问题</Text>
        {recommendedQuestions.slice(0, 3).map((question) => (
          <Button key={question} block onClick={() => submit(question)}>{question}</Button>
        ))}
      </div>

      <TutorQuickActions onAsk={onAsk} />

      <div className="tutor-messages">
        {messages.length === 0 && (
          <div className="tutor-empty">
            <RobotOutlined />
            <Text type="secondary">我会根据当前场景解释概念、纠正误区并生成练习。</Text>
          </div>
        )}
        {messages.map((msg, index) => (
          <div key={`${msg.role}-${index}`} className={`tutor-message tutor-${msg.role}`}>
            <Avatar size={28} icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />} />
            {msg.role === 'assistant' ? <MarkdownRenderer content={stripJsonWrapper(msg.content)} compact /> : <Paragraph>{msg.content}</Paragraph>}
          </div>
        ))}
      </div>

      <Input.TextArea
        value={input}
        onChange={(event) => setInput(event.target.value)}
        onPressEnter={(event) => {
          if (!event.shiftKey) {
            event.preventDefault()
            submit()
          }
        }}
        placeholder="问问 AI 导师..."
        rows={3}
      />
      <Button type="primary" icon={<SendOutlined />} loading={loading} block onClick={() => submit()}>
        发送
      </Button>
    </Card>
  )
}
