import { useState, useCallback } from 'react'
import { Card, Radio, Button, Space, Typography, Tag, Result, Divider } from 'antd'
import { CheckOutlined, CloseOutlined, RightOutlined, BulbOutlined } from '@ant-design/icons'
import MarkdownRenderer from './MarkdownRenderer'

const { Text, Title } = Typography

/**
 * 练习题卡片
 *
 * @param {Object} props
 * @param {Object} props.quiz - 题目数据
 * @param {string} props.quiz.id
 * @param {string} props.quiz.question - 题干（支持 Markdown）
 * @param {Array<{key: string, content: string}>} props.quiz.options - 选项
 * @param {string} props.quiz.answer - 正确答案 key
 * @param {string} props.quiz.explanation - 解析（支持 Markdown）
 * @param {string} props.quiz.difficulty - 难度: easy|medium|hard
 * @param {Function} props.onAnswered - (quizId, isCorrect: boolean) => void
 * @param {boolean} props.showResult - 是否直接显示答案
 */
export default function QuizCard({
  quiz,
  onAnswered,
  showResult = false,
  loading = false,
}) {
  const [selected, setSelected] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  const isCorrect = selected === quiz?.answer

  const difficultyMap = {
    easy: { label: '简单', color: 'success' },
    medium: { label: '中等', color: 'warning' },
    hard: { label: '困难', color: 'error' },
  }

  const handleSubmit = useCallback(() => {
    if (!selected) return
    setSubmitted(true)
    onAnswered?.(quiz.id, isCorrect)
  }, [selected, isCorrect, quiz?.id, onAnswered])

  const handleReset = useCallback(() => {
    setSelected(null)
    setSubmitted(false)
  }, [])

  if (loading) {
    return <Card loading style={{ maxWidth: 800, margin: '0 auto', minHeight: 200 }} />
  }

  if (!quiz) {
    return (
      <Card>
        <Text type="secondary">题目不可用</Text>
      </Card>
    )
  }

  const diff = difficultyMap[quiz.difficulty] || difficultyMap.medium

  return (
    <Card
      title={
        <Space>
          <Tag color={diff.color}>{diff.label}</Tag>
          <Text strong>练习题</Text>
        </Space>
      }
      style={{ maxWidth: 800, margin: '0 auto' }}
    >
      {/* 题干 */}
      <div style={{ marginBottom: 16 }}>
        <MarkdownRenderer content={quiz.question} compact />
      </div>

      {/* 选项 */}
      <Radio.Group
        value={selected}
        onChange={(e) => !submitted && setSelected(e.target.value)}
        style={{ width: '100%' }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          {quiz.options?.map((opt) => {
            let optionStyle = {}
            if (submitted) {
              if (opt.key === quiz.answer) {
                optionStyle = { color: '#52c41a', fontWeight: 'bold' }
              } else if (opt.key === selected && !isCorrect) {
                optionStyle = { color: '#ff4d4f' }
              }
            }
            return (
              <Radio key={opt.key} value={opt.key} style={optionStyle}>
                <span style={optionStyle}>
                  {opt.key.toUpperCase()}. {opt.content}
                </span>
              </Radio>
            )
          })}
        </Space>
      </Radio.Group>

      {/* 操作按钮 */}
      {!submitted ? (
        <div style={{ marginTop: 16 }}>
          <Button
            type="primary"
            icon={<RightOutlined />}
            onClick={handleSubmit}
            disabled={!selected}
          >
            提交答案
          </Button>
        </div>
      ) : (
        <div style={{ marginTop: 16 }}>
          <Result
            status={isCorrect ? 'success' : 'error'}
            title={isCorrect ? '回答正确！' : '回答错误'}
            subTitle={
              quiz.explanation && (
                <div style={{ textAlign: 'left' }}>
                  <Divider />
                  <Text strong>
                    <BulbOutlined /> 解析：
                  </Text>
                  <MarkdownRenderer content={quiz.explanation} compact />
                </div>
              )
            }
            icon={isCorrect ? <CheckOutlined /> : <CloseOutlined />}
          />
          <Button onClick={handleReset}>重新作答</Button>
        </div>
      )}
    </Card>
  )
}
