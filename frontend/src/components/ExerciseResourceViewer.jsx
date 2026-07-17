import { useState, useCallback } from 'react'
import { Button, Card, Progress, Radio, Checkbox, Input, Space, Tag, Typography, message, Result } from 'antd'
import { CheckCircleFilled, CloseCircleFilled, BulbOutlined, EditOutlined } from '@ant-design/icons'
import { normalizeLegacyContent } from '../utils/resourceNormalizer'

const { Text, Title, Paragraph } = Typography

const TYPE_LABELS = {
  single_choice: '单选题', multiple_choice: '多选题', true_false: '判断题',
  fill_blank: '填空题', short_answer: '简答题', code: '编程题',
}

/**
 * Interactive exercise viewer — answer, submit, feedback, scoring.
 */
export default function ExerciseResourceViewer({ resource }) {
  const content = normalizeLegacyContent(resource) || resource?.content
  const questions = content?.questions || (Array.isArray(content) ? content : [])
  const instructions = content?.instructions || ''

  const [answers, setAnswers] = useState({})
  const [submitted, setSubmitted] = useState({})
  const [score, setScore] = useState(null)

  const handleSelect = useCallback((qId, value) => {
    if (submitted[qId]) return
    setAnswers((prev) => ({ ...prev, [qId]: value }))
  }, [submitted])

  const handleSubmitOne = useCallback((q) => {
    setSubmitted((prev) => {
      const next = { ...prev, [q.id]: true }
      const submittedCount = Object.keys(next).length
      if (submittedCount === questions.length) {
        // Calculate total score
        let correct = 0
        questions.forEach((q2) => {
          const userAns = answers[q2.id]
          const correctAns = q2.correct_answer
          const isCorrect = Array.isArray(correctAns)
            ? arraysEqual((Array.isArray(userAns) ? userAns : [userAns]).sort(), correctAns.sort())
            : String(userAns).toUpperCase() === String(correctAns).toUpperCase()
          if (isCorrect) correct++
        })
        setScore({ correct, total: questions.length })
      }
      return next
    })
  }, [questions, answers])

  const handleSubmitAll = () => {
    questions.forEach((q) => {
      if (!submitted[q.id] && answers[q.id] != null) {
        handleSubmitOne(q)
      }
    })
    // Submit remaining
    questions.forEach((q) => {
      if (!submitted[q.id]) {
        setSubmitted((prev) => ({ ...prev, [q.id]: true }))
      }
    })
    let correct = 0
    questions.forEach((q) => {
      const userAns = answers[q.id]
      const correctAns = q.correct_answer
      const isCorrect = Array.isArray(correctAns)
        ? arraysEqual((Array.isArray(userAns) ? userAns : [userAns] || []).sort(), correctAns.sort())
        : String(userAns || '').toUpperCase() === String(correctAns || '').toUpperCase()
      if (isCorrect) correct++
    })
    setScore({ correct, total: questions.length })
  }

  const handleReset = () => {
    setAnswers({})
    setSubmitted({})
    setScore(null)
  }

  if (!questions.length) {
    return <Result status="warning" title="该练习暂无题目" subTitle="资源内容格式可能异常" />
  }

  const allSubmitted = questions.every((q) => submitted[q.id])

  return (
    <div style={{ maxWidth: 780, margin: '0 auto' }}>
      {instructions && (
        <Card size="small" style={{ marginBottom: 20, borderRadius: 12, background: '#F3F0FF', border: '1px solid #E5E7EB' }}>
          <Text style={{ color: '#6C5CE7', fontSize: 13 }}><EditOutlined /> {instructions}</Text>
        </Card>
      )}

      {score && (
        <Card size="small" style={{ marginBottom: 20, borderRadius: 12, background: score.correct === score.total ? '#F0FDF4' : '#FFF7ED', border: '1px solid #E5E7EB' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={4} style={{ color: score.correct === score.total ? '#22C55E' : '#F59E0B', margin: 0 }}>
              {score.correct} / {score.total} 正确
            </Title>
            <Progress percent={Math.round((score.correct / score.total) * 100)} strokeColor={score.correct === score.total ? '#22C55E' : '#F59E0B'} style={{ maxWidth: 300, margin: '8px auto' }} />
          </div>
        </Card>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {questions.map((q, qi) => {
          const userAns = answers[q.id]
          const isSubmitted = submitted[q.id]
          const correctAns = q.correct_answer
          const isCorrect = Array.isArray(correctAns)
            ? arraysEqual((Array.isArray(userAns) ? userAns : [userAns] || []).sort(), (correctAns || []).sort())
            : String(userAns || '').toUpperCase() === String(correctAns || '').toUpperCase()

          return (
            <Card key={q.id || qi} size="small" style={{ borderRadius: 12, border: isSubmitted ? (isCorrect ? '1.5px solid #22C55E' : '1.5px solid #EF4444') : '1px solid #E5E7EB' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 10 }}>
                <Tag style={{ borderRadius: 6 }}>{qi + 1}</Tag>
                <Tag color="purple" style={{ borderRadius: 6 }}>{TYPE_LABELS[q.type] || '单选题'}</Tag>
                {q.difficulty && <Tag style={{ borderRadius: 6 }}>{q.difficulty}</Tag>}
              </div>
              <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 10 }}>{q.stem || q.question}</Text>

              {q.type === 'single_choice' || q.type === 'true_false' || !q.type ? (
                <Radio.Group value={userAns} onChange={(e) => handleSelect(q.id, e.target.value)} disabled={isSubmitted} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {(q.options || []).map((o, oi) => {
                    const key = typeof o === 'string' ? String.fromCharCode(65 + oi) : (o.key || String.fromCharCode(65 + oi))
                    const text = typeof o === 'string' ? o : (o.text || o.content || '')
                    let st = {}
                    if (isSubmitted && (correctAns || []).includes(key)) st = { color: '#22C55E', fontWeight: 'bold' }
                    if (isSubmitted && userAns === key && !(correctAns || []).includes(key)) st = { color: '#EF4444' }
                    return <Radio key={key} value={key} style={st}>{key}. {text}</Radio>
                  })}
                </Radio.Group>
              ) : q.type === 'multiple_choice' ? (
                <Checkbox.Group value={userAns || []} onChange={(v) => handleSelect(q.id, v)} disabled={isSubmitted} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {(q.options || []).map((o, oi) => {
                    const key = typeof o === 'string' ? String.fromCharCode(65 + oi) : (o.key || String.fromCharCode(65 + oi))
                    const text = typeof o === 'string' ? o : (o.text || o.content || '')
                    return <Checkbox key={key} value={key}>{key}. {text}</Checkbox>
                  })}
                </Checkbox.Group>
              ) : (
                <Input.TextArea value={userAns || ''} onChange={(e) => handleSelect(q.id, e.target.value)} disabled={isSubmitted} rows={3} placeholder="请输入答案..." style={{ borderRadius: 8 }} />
              )}

              {isSubmitted && (
                <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 10, background: isCorrect ? '#F0FDF4' : '#FFF2F0' }}>
                  <Text style={{ color: isCorrect ? '#22C55E' : '#EF4444', display: 'block', marginBottom: 4 }}>
                    {isCorrect ? <><CheckCircleFilled /> 正确</> : <><CloseCircleFilled /> 错误 · 正确答案：{Array.isArray(correctAns) ? correctAns.join(', ') : correctAns}</>}
                  </Text>
                  {q.explanation && (
                    <Text style={{ fontSize: 12, color: '#6B7280' }}><BulbOutlined /> {q.explanation}</Text>
                  )}
                </div>
              )}

              {!isSubmitted && userAns != null && (
                <Button size="small" type="primary" onClick={() => handleSubmitOne(q)} style={{ marginTop: 10, borderRadius: 6, background: '#6C5CE7' }}>提交</Button>
              )}
            </Card>
          )
        })}
      </div>

      {!allSubmitted && (
        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <Space>
            <Button type="primary" onClick={handleSubmitAll} style={{ borderRadius: 8, background: '#6C5CE7' }}>提交全部答案</Button>
            <Button onClick={handleReset} style={{ borderRadius: 8 }}>重新作答</Button>
          </Space>
        </div>
      )}
      {allSubmitted && (
        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <Button onClick={handleReset} style={{ borderRadius: 8 }}>重新作答</Button>
        </div>
      )}
    </div>
  )
}

function arraysEqual(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b)) return String(a) === String(b)
  if (a.length !== b.length) return false
  const sa = [...a].sort(), sb = [...b].sort()
  return sa.every((v, i) => String(v).toUpperCase() === String(sb[i]).toUpperCase())
}
