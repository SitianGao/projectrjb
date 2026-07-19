import { useState, useRef, useEffect } from 'react'
import { Button, Dropdown, Input, Space, Typography } from 'antd'
import {
  BulbOutlined, DownOutlined, FileTextOutlined, FormOutlined,
  QuestionCircleOutlined, SendOutlined, BranchesOutlined,
} from '@ant-design/icons'
import MarkdownRenderer from '../MarkdownRenderer'

const { Text } = Typography

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

function buildSuggestions(currentTask) {
  const base = [
    '解释当前知识点',
    '生成 3 道例题',
    '换一种方式讲解',
  ]
  if (currentTask?.title) {
    base.unshift(`帮我理解「${currentTask.title.slice(0, 20)}」`)
  }
  return base
}

export default function WorkspaceChatPanel({
  messages, loading, onSend, onConvert, converting,
  currentTask, welcomeMessage,
}) {
  const [value, setValue] = useState('')
  const listRef = useRef(null)

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [messages])

  const submit = () => {
    const text = value.trim()
    if (!text) return
    onSend(text)
    setValue('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const suggestions = buildSuggestions(currentTask)

  return (
    <div className="workspace-chat-panel">
      {/* header */}
      <div className="chat-panel-header">
        <div>
          <Text strong style={{ fontSize: 15 }}>AI 学习导师</Text>
          <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
            正在结合当前课程与学习任务回答
          </Text>
        </div>
      </div>

      {/* messages */}
      <div className="chat-message-list" ref={listRef}>
        {messages.length === 0 && welcomeMessage && (
          <div className="chat-welcome">
            <Text>{welcomeMessage}</Text>
            <div className="chat-welcome-actions">
              <Button onClick={() => onSend('先讲清当前知识点的核心概念')}>先讲核心概念</Button>
              <Button onClick={() => onSend('直接开始代码实践')}>开始代码实践</Button>
              <Button onClick={() => onSend('出3道诊断题检测我的掌握度')}>做诊断题</Button>
            </div>
          </div>
        )}

        {messages.length === 0 && !welcomeMessage && (
          <div className="chat-empty-hint">
            <Text type="secondary">向 AI 导师提问，或使用下方快捷操作开始学习。</Text>
          </div>
        )}

        {messages.map((msg, i) => (
          <div className={`chat-message is-${msg.role}`} key={`${msg.role}-${i}`}>
            <div className="chat-message-avatar">
              {msg.role === 'user' ? '我' : 'AI'}
            </div>
            <div className="chat-message-body">
              <div className="chat-message-content">
                {msg.role === 'assistant' ? (
                  <MarkdownRenderer content={stripJsonWrapper(msg.content)} compact />
                ) : (
                  msg.content?.split('\n').map((line, j) => (
                    line ? <p key={j}>{line}</p> : <br key={j} />
                  ))
                )}
              </div>

              {msg.role === 'assistant' && msg.content && (
                <div className="chat-message-actions">
                  <Button size="small" icon={<QuestionCircleOutlined />}
                    onClick={() => onSend('请继续深入讲解')} disabled={loading}>
                    继续追问
                  </Button>
                  <Button size="small" icon={<BulbOutlined />}
                    onClick={() => onSend('请给我一个具体的例子')} disabled={loading}>
                    举个例子
                  </Button>
                  <Button size="small" icon={<FormOutlined />}
                    onClick={() => onSend('以上内容出一道检测题')} disabled={loading}>
                    生成练习
                  </Button>
                  <Dropdown menu={{
                    items: [
                      { key: 'document', icon: <FileTextOutlined />, label: '转为讲义',
                        onClick: () => onConvert?.(msg.content, 'document') },
                      { key: 'exercise', icon: <FormOutlined />, label: '转为练习',
                        onClick: () => onConvert?.(msg.content, 'exercise') },
                      { key: 'mindmap', icon: <BranchesOutlined />, label: '转为导图',
                        onClick: () => onConvert?.(msg.content, 'mindmap') },
                    ],
                  }} trigger={['click']}>
                    <Button size="small" icon={<DownOutlined />} loading={converting}>更多</Button>
                  </Dropdown>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* dynamic suggestions */}
      <div className="chat-suggestions">
        {suggestions.map((text) => (
          <Button key={text} size="small" onClick={() => onSend(text)} disabled={loading}>
            {text}
          </Button>
        ))}
      </div>

      {/* fixed input */}
      <div className="chat-input-area">
        <Input.TextArea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          autoSize={{ minRows: 2, maxRows: 4 }}
          placeholder={currentTask?.title
            ? `向 AI 导师提问，或输入"帮我生成一道${currentTask.title.slice(0, 15)}练习题"...`
            : '向 AI 导师提问，或输入"帮我生成一道练习题"...'}
        />
        <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={submit}>
          发送
        </Button>
      </div>
    </div>
  )
}
