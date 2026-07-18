import { useNavigate } from 'react-router-dom'
import { Button, Space, Typography } from 'antd'
import {
  ArrowLeftOutlined,
  BranchesOutlined,
} from '@ant-design/icons'
import CourseProgress from './CourseProgress'

const { Text } = Typography

const CN_NUMBERS = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']

function formatStageLabel(stageIndex) {
  const num = Number(stageIndex) || 1
  if (num >= 0 && num <= 10) return `阶段${CN_NUMBERS[num]}`
  return `阶段${num}`
}

/**
 * Compact course context bar shown above the three-column learning layout.
 */
export default function CourseContextHeader({
  courseName = '人工智能',
  courseId,
  stageTitle = '',
  stageDescription = '',
  stageIndex = 1,
  completedTasks = 0,
  totalTasks = 1,
}) {
  const navigate = useNavigate()
  const courseLabel = courseName.length > 10 ? courseName.slice(0, 10) + '…' : courseName
  const stageLabel = formatStageLabel(stageIndex)

  return (
    <div style={{
      background: '#FFFFFF',
      borderRadius: 16,
      padding: '14px 24px',
      marginBottom: 16,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 24,
      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      border: '1px solid #E5E7EB',
      flexWrap: 'wrap',
    }}>
      {/* Left: info */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, flex: 1, minWidth: 0 }}>
        <div style={{ minWidth: 0 }}>
          <Text strong style={{ fontSize: 15, color: '#111827' }}>
            {courseName}
          </Text>
          {stageTitle && (
            <Text style={{ fontSize: 13, color: '#6B7280', marginLeft: 10 }}>
              当前阶段：{stageLabel}，{stageTitle}
            </Text>
          )}
        </div>
      </div>

      {/* Right: progress + actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexShrink: 0 }}>
        <div style={{ width: 180 }}>
          <Text style={{ display: 'block', fontSize: 12, color: '#6B7280', marginBottom: 4 }}>
            阶段进度
          </Text>
          <CourseProgress
            completed={completedTasks}
            total={totalTasks}
            height={6}
          />
        </div>

        <Space size={8}>
          <Button
            size="small"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/home')}
            style={{
              borderRadius: 8,
              color: '#6B7280',
              borderColor: '#E5E7EB',
            }}
          >
            返回学习首页
          </Button>
          {courseId && (
            <Button
              size="small"
              type="primary"
              icon={<BranchesOutlined />}
              onClick={() => navigate(`/course/${courseId}/path`)}
              style={{
                borderRadius: 8,
                background: '#6C5CE7',
                borderColor: '#6C5CE7',
              }}
            >
              查看完整学习路径
            </Button>
          )}
        </Space>
      </div>
    </div>
  )
}
