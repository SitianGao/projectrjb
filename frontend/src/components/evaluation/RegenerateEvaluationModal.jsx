import { Alert, Button, Modal, Space, Typography } from 'antd'
import { useState } from 'react'

const { Paragraph } = Typography

export default function RegenerateEvaluationModal({ open, onCancel, onOk, onForceRegen, loading }) {
  const [showForce, setShowForce] = useState(false)

  return (
    <Modal
      title="重新评估"
      open={open}
      onCancel={() => { onCancel(); setShowForce(false) }}
      footer={
        <Space>
          <Button onClick={() => { onCancel(); setShowForce(false) }}>取消</Button>
          {!showForce && <Button type="primary" onClick={onOk} loading={loading}>确认重新评估</Button>}
        </Space>
      }
    >
      <Paragraph>
        系统会检查上次评估后是否存在新的学习任务、答题或测评记录。
        如果输入数据完全相同，将不会生成重复报告。
      </Paragraph>
      <Paragraph type="secondary">
        评估过程：收集学习记录 → 计算指标 → AI 分析薄弱点 → 更新画像 → 检查学习路径
      </Paragraph>
      {!showForce ? (
        <Button type="link" danger onClick={() => { setShowForce(true); if (onForceRegen) onForceRegen() }}>
          即使无新数据也强制重新评估
        </Button>
      ) : (
        <Alert type="warning" showIcon message="强制重新评估将生成新版本报告"
          action={<Button size="small" danger onClick={onOk} loading={loading}>确认强制评估</Button>} />
      )}
    </Modal>
  )
}
