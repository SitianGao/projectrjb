import { useState, useMemo } from 'react'
import { Typography, Input, Button, Alert, Space, Tag } from 'antd'
import { EditOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'

const { Text, Paragraph } = Typography

/**
 * 代码补全组件 — 在代码中高亮空白位置，让学生填写。
 * 用于 code_completion 模式。
 */
export function CodeBlanks({
  codeWithBlanks = '',
  blanks = [],
  onSubmit,
  showAnswers = false,
}) {
  const [answers, setAnswers] = useState(() => {
    const init = {}
    blanks.forEach((b, i) => {
      init[b.position || i] = ''
    })
    return init
  })
  const [submitted, setSubmitted] = useState(false)

  const handleAnswerChange = (key, value) => {
    setAnswers((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = () => {
    setSubmitted(true)
    onSubmit?.(answers)
  }

  const handleReset = () => {
    const init = {}
    blanks.forEach((b, i) => {
      init[b.position || i] = ''
    })
    setAnswers(init)
    setSubmitted(false)
  }

  // 将代码拆分为片段和空白
  const segments = useMemo(() => {
    if (!codeWithBlanks) return []
    const parts = []
    let remaining = codeWithBlanks
    let blankIndex = 0

    while (remaining.length > 0) {
      const blankMarker = '______'
      const idx = remaining.indexOf(blankMarker)
      if (idx === -1) {
        parts.push({ type: 'code', text: remaining })
        break
      }
      if (idx > 0) {
        parts.push({ type: 'code', text: remaining.slice(0, idx) })
      }
      const blank = blanks[blankIndex] || {}
      parts.push({
        type: 'blank',
        key: blank.position || blankIndex,
        hint: blank.hint || '',
        answer: blank.answer || '',
      })
      blankIndex++
      remaining = remaining.slice(idx + blankMarker.length)
    }
    return parts
  }, [codeWithBlanks, blanks])

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 8,
      overflow: 'hidden',
      background: 'var(--bg-card)',
    }}>
      <div style={{
        padding: '8px 14px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-page)',
      }}>
        <Space>
          <EditOutlined style={{ color: '#89b4fa' }} />
          <Text strong style={{ fontSize: 13 }}>代码补全</Text>
          <Tag>{blanks.length} 处空白</Tag>
        </Space>
      </div>

      <div style={{
        padding: 14,
        fontFamily: "'Cascadia Code', 'Fira Code', monospace",
        fontSize: 13,
        lineHeight: 1.8,
        background: '#1e1e2e',
        color: '#cdd6f4',
      }}>
        {segments.map((seg, i) => {
          if (seg.type === 'code') {
            return (
              <pre key={i} style={{
                margin: 0,
                whiteSpace: 'pre-wrap',
                display: 'inline',
              }}>
                {seg.text}
              </pre>
            )
          }

          const userAnswer = answers[seg.key] || ''
          const isCorrect = submitted && showAnswers &&
            seg.answer && userAnswer.trim() === seg.answer.trim()

          return (
            <span key={i} style={{ position: 'relative', display: 'inline-block' }}>
              <input
                value={userAnswer}
                onChange={(e) => handleAnswerChange(seg.key, e.target.value)}
                placeholder={seg.hint || '填写代码'}
                disabled={submitted}
                style={{
                  width: Math.max(100, userAnswer.length * 9 + 20),
                  padding: '2px 6px',
                  border: submitted
                    ? isCorrect
                      ? '2px solid #52c41a'
                      : '2px solid #ff4d4f'
                    : '2px solid #89b4fa',
                  borderRadius: 4,
                  background: submitted
                    ? isCorrect ? '#f6ffed' : '#fff2f0'
                    : '#2b2b3d',
                  color: '#cdd6f4',
                  fontFamily: 'inherit',
                  fontSize: 'inherit',
                  outline: 'none',
                  transition: 'all 0.2s',
                }}
              />
              {submitted && showAnswers && !isCorrect && seg.answer && (
                <Text
                  style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    fontSize: 11,
                    color: '#52c41a',
                    whiteSpace: 'nowrap',
                  }}
                >
                  参考答案: {seg.answer}
                </Text>
              )}
            </span>
          )
        })}
      </div>

      <div style={{
        padding: '10px 14px',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        gap: 8,
      }}>
        <Button
          type="primary"
          size="small"
          onClick={handleSubmit}
          disabled={submitted}
        >
          提交答案
        </Button>
        <Button size="small" onClick={handleReset}>
          重置
        </Button>
      </div>
    </div>
  )
}

/**
 * 错误诊断组件 — 展示有 bug 的代码，让学生修改。
 * 用于 error_diagnosis 模式。
 */
export function ErrorDiagnosis({
  buggyCode = '',
  bugDescription = '',
  fixHint = '',
  onFix,
}) {
  const [userCode, setUserCode] = useState(buggyCode)
  const [showHint, setShowHint] = useState(false)

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 8,
      overflow: 'hidden',
      background: 'var(--bg-card)',
    }}>
      <div style={{
        padding: '8px 14px',
        borderBottom: '1px solid var(--border)',
        background: '#fff2f0',
      }}>
        <Space>
          <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
          <Text strong style={{ fontSize: 13, color: '#cf1322' }}>错误诊断</Text>
        </Space>
      </div>

      {bugDescription && (
        <Alert
          message="问题描述"
          description={bugDescription}
          type="warning"
          showIcon
          style={{ margin: 12, marginBottom: 0 }}
        />
      )}

      <div style={{ padding: 12 }}>
        <pre style={{
          background: '#1e1e2e',
          color: '#cdd6f4',
          padding: 14,
          borderRadius: 8,
          fontSize: 13,
          lineHeight: 1.6,
          maxHeight: 300,
          overflow: 'auto',
          margin: 0,
          whiteSpace: 'pre-wrap',
        }}>
          {buggyCode}
        </pre>
      </div>

      <div style={{ padding: '0 14px 12px' }}>
        <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}>
          修正后的代码：
        </Text>
        <textarea
          value={userCode}
          onChange={(e) => setUserCode(e.target.value)}
          style={{
            width: '100%',
            minHeight: 150,
            padding: 12,
            fontFamily: "'Cascadia Code', 'Fira Code', monospace",
            fontSize: 13,
            lineHeight: 1.6,
            border: '1px solid #d9d9d9',
            borderRadius: 6,
            resize: 'vertical',
            background: '#1e1e2e',
            color: '#cdd6f4',
          }}
        />
      </div>

      {showHint && fixHint && (
        <Alert
          message="提示"
          description={fixHint}
          type="info"
          showIcon
          style={{ margin: '0 14px 12px' }}
        />
      )}

      <div style={{
        padding: '10px 14px',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        gap: 8,
      }}>
        <Button
          type="primary"
          size="small"
          onClick={() => onFix?.(userCode)}
        >
          运行修正代码
        </Button>
        <Button size="small" onClick={() => setShowHint(!showHint)}>
          {showHint ? '隐藏提示' : '查看提示'}
        </Button>
      </div>
    </div>
  )
}
