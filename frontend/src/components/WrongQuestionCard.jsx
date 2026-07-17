import { useState } from 'react'
import { Button, Card, Dropdown, Modal, Radio, Space, Tag, Typography, message } from 'antd'
import {
  CheckCircleOutlined, CloseCircleOutlined, DownOutlined, MoreOutlined,
  ExclamationCircleOutlined, RightOutlined, ClockCircleOutlined,
} from '@ant-design/icons'
import MarkdownRenderer from './MarkdownRenderer'

const { Text, Paragraph } = Typography

const PRIORITY_CONFIG = {
  high: { color: '#EF4444', label: '高优先级' },
  medium: { color: '#F59E0B', label: '中优先级' },
  low: { color: '#22C55E', label: '低优先级' },
}

export default function WrongQuestionCard({
  item,
  onReview,
  onManualMaster,
  onRemove,
  reviewing,
}) {
  const [expanded, setExpanded] = useState(false)
  const [showReviewModal, setShowReviewModal] = useState(false)
  const [showMasterConfirm, setShowMasterConfirm] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  const priority = PRIORITY_CONFIG[item.priority] || PRIORITY_CONFIG.medium
  const masteryProgress = Math.min(item.correct_streak || 0, 2)
  const statusColor = item.status === 'mastered' ? '#22C55E' : item.status === 'reviewing' ? '#F59E0B' : '#EF4444'

  const handleSubmitAnswer = () => {
    if (!selectedAnswer) { message.warning('请选择一个答案'); return }
    onReview?.(item, selectedAnswer).then((result) => {
      setSubmitted(true)
      if (result?.is_correct) {
        message.success('回答正确！')
      } else {
        message.error('回答错误')
      }
    })
  }

  const handleManualMasterConfirm = () => {
    onManualMaster?.(item)
    setShowMasterConfirm(false)
  }

  return (
    <Card
      size="small"
      style={{
        borderRadius: 12,
        border: `1px solid #E5E7EB`,
        borderLeft: `3px solid ${statusColor}`,
        marginBottom: 10,
        minWidth: 0,
      }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap' }}>
        <Space size={6} wrap>
          {item.topic && <Tag color="purple" style={{ borderRadius: 6 }}>{item.topic}</Tag>}
          {item.question_type && <Tag style={{ borderRadius: 6 }}>{item.question_type === 'choice' ? '选择题' : item.question_type}</Tag>}
          {item.stage_title && <Tag style={{ borderRadius: 6 }}>{item.stage_title}</Tag>}
        </Space>
        <Space size={4}>
          {item.wrong_count > 0 && (
            <Tag color="red" style={{ borderRadius: 6 }}>累计答错 {item.wrong_count} 次</Tag>
          )}
          {masteryProgress > 0 && (
            <Tag color={masteryProgress >= 2 ? 'success' : 'orange'} style={{ borderRadius: 6 }}>
              <CheckCircleOutlined /> {masteryProgress}/2
            </Tag>
          )}
        </Space>
      </div>

      {/* Question excerpt */}
      <div style={{ marginTop: 8, marginBottom: 8 }}>
        <Text style={{ fontSize: 13, color: '#111827', lineHeight: 1.6 }}>
          {item.question ? (
            item.question.length > 80 ? item.question.slice(0, 80) + '…' : item.question
          ) : '题目加载异常'}
        </Text>
      </div>

      {/* Meta info */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 11, color: '#9CA3AF', marginBottom: 8 }}>
        {item.last_wrong_at && <span>上次答错：{new Date(item.last_wrong_at).toLocaleDateString('zh-CN')}</span>}
        {item.next_review_at && (
          <span style={{ color: item.next_review_at <= new Date().toISOString().split('T')[0] ? '#EF4444' : '#9CA3AF' }}>
            <ClockCircleOutlined /> 下次复习：{new Date(item.next_review_at).toLocaleDateString('zh-CN')}
          </span>
        )}
      </div>

      {/* Action buttons */}
      <Space size={8}>
        <Button
          type="primary"
          size="small"
          icon={<RightOutlined />}
          onClick={() => setShowReviewModal(true)}
          loading={reviewing}
          style={{ borderRadius: 8, background: '#6C5CE7', borderColor: '#6C5CE7' }}
        >
          重新作答
        </Button>
        <Button
          size="small"
          icon={expanded ? <DownOutlined style={{ transform: 'rotate(180deg)' }} /> : <DownOutlined />}
          onClick={() => setExpanded(!expanded)}
          style={{ borderRadius: 8 }}
        >
          查看解析
        </Button>
        <Dropdown menu={{ items: [
          { key: 'master', label: '手动标记为掌握', icon: <CheckCircleOutlined />, onClick: () => setShowMasterConfirm(true) },
          { key: 'remove', label: '移出错题本', icon: <CloseCircleOutlined />, danger: true, onClick: () => onRemove?.(item) },
        ]}} trigger={['click']}>
          <Button size="small" icon={<MoreOutlined />} style={{ borderRadius: 8 }} />
        </Dropdown>
      </Space>

      {/* Expanded explanation */}
      {expanded && (
        <div style={{ marginTop: 14, padding: '14px 16px', background: '#F9FAFB', borderRadius: 10, border: '1px solid #E5E7EB' }}>
          <div style={{ marginBottom: 8 }}>
            <Text style={{ color: '#EF4444', fontSize: 12 }}><CloseCircleOutlined /> 你的答案：{item.user_answer || '--'}</Text>
            <br />
            <Text style={{ color: '#22C55E', fontSize: 12 }}><CheckCircleOutlined /> 正确答案：{item.correct_answer}</Text>
          </div>
          {item.explanation && (
            <div>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>解析</Text>
              <MarkdownRenderer content={item.explanation} compact />
            </div>
          )}
          {item.recommended_resources?.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>推荐资源</Text>
              {item.recommended_resources.map((r, i) => (
                <Tag key={i} color="purple" style={{ borderRadius: 6, fontSize: 11 }}>{r.title || r}</Tag>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Review Modal */}
      <Modal
        title="重新作答"
        open={showReviewModal}
        onCancel={() => { setShowReviewModal(false); setSelectedAnswer(null); setSubmitted(false) }}
        footer={
          submitted ? [
            <Button key="close" onClick={() => { setShowReviewModal(false); setSelectedAnswer(null); setSubmitted(false) }}>关闭</Button>,
          ] : [
            <Button key="cancel" onClick={() => { setShowReviewModal(false); setSelectedAnswer(null) }}>取消</Button>,
            <Button key="submit" type="primary" onClick={handleSubmitAnswer} style={{ borderRadius: 8, background: '#6C5CE7' }}>提交答案</Button>,
          ]
        }
        width={520}
      >
        <div style={{ marginBottom: 16 }}>
          <Text style={{ fontSize: 14, lineHeight: 1.7 }}>{item.question}</Text>
        </div>
        {item.options?.length > 0 ? (
          <Radio.Group value={selectedAnswer} onChange={(e) => !submitted && setSelectedAnswer(e.target.value)}>
            <Space direction="vertical">
              {item.options.map((opt, i) => {
                const key = typeof opt === 'string' ? String.fromCharCode(65 + i) : (opt.key || String.fromCharCode(65 + i))
                const text = typeof opt === 'string' ? opt : (opt.content || opt.text || '')
                let style = {}
                if (submitted && key === item.correct_answer) style = { color: '#22C55E', fontWeight: 'bold' }
                if (submitted && key === selectedAnswer && key !== item.correct_answer) style = { color: '#EF4444' }
                return <Radio key={key} value={key} disabled={submitted} style={style}>{key}. {text}</Radio>
              })}
            </Space>
          </Radio.Group>
        ) : (
          <Text type="secondary">该题目暂无选项数据</Text>
        )}
        {submitted && (
          <div style={{ marginTop: 16, padding: 12, background: '#F9FAFB', borderRadius: 8 }}>
            <Text strong style={{ color: selectedAnswer === item.correct_answer ? '#22C55E' : '#EF4444', display: 'block', marginBottom: 6 }}>
              {selectedAnswer === item.correct_answer ? '回答正确！' : '回答错误'}
            </Text>
            {item.explanation && <MarkdownRenderer content={item.explanation} compact />}
          </div>
        )}
      </Modal>

      {/* Manual master confirm */}
      <Modal
        title="手动标记为掌握"
        open={showMasterConfirm}
        onCancel={() => setShowMasterConfirm(false)}
        onOk={handleManualMasterConfirm}
        okText="确认标记"
        okButtonProps={{ danger: true }}
        width={400}
      >
        <Paragraph>
          手动标记不会计入自动掌握记录，确定继续吗？
        </Paragraph>
      </Modal>
    </Card>
  )
}
