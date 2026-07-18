import { useNavigate } from 'react-router-dom'
import { Button, Space, Typography } from 'antd'
import {
  BranchesOutlined,
  InboxOutlined,
} from '@ant-design/icons'

const { Text, Title } = Typography

/**
 * Page header with title and action buttons.
 */
export default function CoursePathHeader({
  courseName = '人工智能',
  courseId,
  onContinueStage,
  loading = false,
}) {
  const navigate = useNavigate()

  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: 16,
      padding: '20px 28px',
      border: '1px solid var(--border)',
      marginBottom: 24,
      maxWidth: 1440,
      margin: '0 auto 24px',
    }}>
      {/* Title row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <Title level={4} style={{ margin: 0, color: 'var(--text-primary)' }}>
            {courseName} 学习路径
          </Title>
        </div>

        {/* Action buttons */}
        <Space size={8} wrap style={{ flexShrink: 0 }}>
          <Button
            type="primary"
            icon={<BranchesOutlined />}
            onClick={onContinueStage}
            loading={loading}
            style={{
              borderRadius: 8,
              background: '#6C5CE7',
              borderColor: '#6C5CE7',
            }}
          >
            继续当前阶段
          </Button>
          <Button
            icon={<InboxOutlined />}
            onClick={() => navigate(courseId ? `/course/${courseId}/wrongbook` : '/wrong-book')}
            style={{ borderRadius: 8 }}
          >
            错题本
          </Button>
        </Space>
      </div>
    </div>
  )
}
