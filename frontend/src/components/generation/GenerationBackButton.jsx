import { ArrowLeftOutlined } from '@ant-design/icons'
import { Button } from 'antd'
import { useNavigate } from 'react-router-dom'

export default function GenerationBackButton({ to = '/home', label = '返回学习首页' }) {
  const navigate = useNavigate()

  return (
    <div className="gen-back-btn">
      <Button
        type="text"
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate(to, { replace: true })}
        style={{
          color: '#6B7280',
          fontSize: 14,
          fontWeight: 500,
          padding: '6px 14px',
          borderRadius: 10,
          background: 'rgba(255,255,255,0.6)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(0,0,0,0.06)',
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = '#6C5CE7'
          e.currentTarget.style.background = 'rgba(255,255,255,0.9)'
          e.currentTarget.style.borderColor = 'rgba(108,92,231,0.2)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = '#6B7280'
          e.currentTarget.style.background = 'rgba(255,255,255,0.6)'
          e.currentTarget.style.borderColor = 'rgba(0,0,0,0.06)'
        }}
      >
        {label}
      </Button>
    </div>
  )
}
