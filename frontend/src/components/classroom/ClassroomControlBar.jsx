import { useState } from 'react'
import { Button, message, Space, Tooltip } from 'antd'
import {
  ArrowLeftOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  FlagOutlined,
  ExclamationCircleOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons'

export default function ClassroomControlBar({
  isFirst,
  isLast,
  completing,
  onPrev,
  onNext,
  onComplete,
  onMarkDifficult,
  onAddToWrongBook,
  onViewResources,
  isQuizTask,
}) {
  const [markLoading, setMarkLoading] = useState(false)
  const [wrongBookLoading, setWrongBookLoading] = useState(false)

  const handleMarkDifficult = async () => {
    setMarkLoading(true)
    try {
      if (onMarkDifficult) await onMarkDifficult()
      else message.success('已标记为困难，系统将调整后续学习路径')
    } finally {
      setMarkLoading(false)
    }
  }

  const handleAddToWrongBook = async () => {
    setWrongBookLoading(true)
    try {
      if (onAddToWrongBook) await onAddToWrongBook()
      else message.success('已加入错题本')
    } finally {
      setWrongBookLoading(false)
    }
  }

  return (
    <div
      style={{
        height: 52,
        flexShrink: 0,
        background: 'rgba(255,255,255,0.9)',
        backdropFilter: 'blur(12px)',
        borderTop: '1px solid rgba(0,0,0,0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        gap: 16,
        zIndex: 40,
      }}
    >
      {/* Left group: navigation */}
      <Space size={10}>
        <Button
          icon={<ArrowLeftOutlined />}
          disabled={isFirst}
          onClick={onPrev}
          style={{
            borderRadius: 10,
            border: '1px solid rgba(0,0,0,0.1)',
            fontWeight: 500,
          }}
        >
          上一步
        </Button>

        {isLast ? (
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={onComplete}
            loading={completing}
            style={{
              borderRadius: 10,
              background: 'linear-gradient(135deg, #6C5CE7, #8B7CF7)',
              border: 'none',
              fontWeight: 600,
            }}
          >
            完成本页并继续
          </Button>
        ) : (
          <Button
            type="primary"
            icon={<ArrowRightOutlined />}
            onClick={onNext}
            style={{
              borderRadius: 10,
              background: 'linear-gradient(135deg, #6C5CE7, #8B7CF7)',
              border: 'none',
              fontWeight: 600,
            }}
          >
            下一步
          </Button>
        )}
      </Space>

      {/* Right group: utility actions */}
      <Space size={8}>
        {onViewResources && (
          <Tooltip title="查看阶段资源">
            <Button
              icon={<FolderOpenOutlined />}
              style={{
                borderRadius: 10,
                border: '1px solid rgba(0,0,0,0.08)',
                color: '#6B7280',
                fontSize: 13,
              }}
              onClick={onViewResources}
            >
              查看阶段资源
            </Button>
          </Tooltip>
        )}

        <Tooltip title="标记此处为学习难点">
          <Button
            icon={<FlagOutlined />}
            loading={markLoading}
            onClick={handleMarkDifficult}
            style={{
              borderRadius: 10,
              border: '1px solid rgba(245,158,11,0.2)',
              color: '#D97706',
              fontSize: 13,
            }}
          >
            标记不会
          </Button>
        </Tooltip>

        {isQuizTask && (
          <Tooltip title="加入错题本以便复习">
            <Button
              icon={<ExclamationCircleOutlined />}
              loading={wrongBookLoading}
              onClick={handleAddToWrongBook}
              style={{
                borderRadius: 10,
                border: '1px solid rgba(239,68,68,0.2)',
                color: '#EF4444',
                fontSize: 13,
              }}
            >
              加入错题本
            </Button>
          </Tooltip>
        )}
      </Space>
    </div>
  )
}
