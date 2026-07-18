import { useNavigate } from 'react-router-dom'
import { Button, Typography } from 'antd'
import { InboxOutlined } from '@ant-design/icons'

const { Title } = Typography

export default function CoursePathHeader({ courseName = '人工智能', courseId }) {
  const navigate = useNavigate()

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '16px 20px',
      background: 'var(--bg-card)',
      borderRadius: 12,
      border: '1px solid var(--border)',
    }}>
      <Title level={4} style={{ margin: 0, color: 'var(--text-primary)' }}>
        {courseName} 学习路径
      </Title>
      <Button
        icon={<InboxOutlined />}
        onClick={() => navigate(courseId ? `/course/${courseId}/wrongbook` : '/wrong-book')}
        style={{ borderRadius: 8 }}
      >
        错题本
      </Button>
    </div>
  )
}
