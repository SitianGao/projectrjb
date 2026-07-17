import { Modal, Typography } from 'antd'

const { Paragraph } = Typography

export default function RegenerateEvaluationModal({ open, onCancel, onOk, loading }) {
  return (
    <Modal
      title="重新评估"
      open={open}
      onCancel={onCancel}
      onOk={onOk}
      okText="确认重新评估"
      cancelText="取消"
      confirmLoading={loading}
    >
      <Paragraph>
        系统会先检查上次评估后是否存在新的学习任务、测评、答题或错题复习记录。
        如果输入数据完全相同，将不会生成重复报告。
      </Paragraph>
    </Modal>
  )
}
