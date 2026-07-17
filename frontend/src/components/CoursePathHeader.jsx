import { useNavigate } from 'react-router-dom'
import { Breadcrumb, Button, Space, Tag, Typography } from 'antd'
import {
  ArrowLeftOutlined,
  BranchesOutlined,
  HomeOutlined,
  InboxOutlined,
  ReloadOutlined,
  SwapOutlined,
} from '@ant-design/icons'

const { Text, Title } = Typography

/**
 * Page header with breadcrumb, title, course context summary, and action buttons.
 * "Continue Current Stage" is the primary CTA.
 */
export default function CoursePathHeader({
  courseName = '人工智能',
  courseId,
  currentStageTitle = '',
  currentStageId,
  totalStages = 0,
  completedTasks = 0,
  totalTasks = 0,
  masteryPercent = 0,
  onRegenerate,
  onContinueStage,
  loading = false,
}) {
  const navigate = useNavigate()

  return (
    <div style={{
      background: '#FFFFFF',
      borderRadius: 16,
      padding: '20px 28px',
      border: '1px solid #E5E7EB',
      marginBottom: 24,
      maxWidth: 1440,
      margin: '0 auto 24px',
    }}>
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { title: <><HomeOutlined style={{ marginRight: 2 }} />学习首页</>, onClick: () => navigate('/home') },
          { title: '我的课程', onClick: () => navigate('/courses') },
          { title: courseName, onClick: () => courseId && navigate(`/course/${courseId}`) },
          { title: '学习路径' },
        ]}
        style={{ fontSize: 13, marginBottom: 12 }}
      />

      {/* Title row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <Title level={4} style={{ margin: 0, color: '#111827' }}>
            {courseName} 个性化学习路径
          </Title>
          <Text style={{ fontSize: 13, color: '#6B7280', marginTop: 4, display: 'block' }}>
            基于你的学习目标、基础测评、学习记录和错题情况自动生成
          </Text>

          {/* Summary tags */}
          <Space size={8} wrap style={{ marginTop: 12 }}>
            <Tag style={{ borderRadius: 6 }}>当前：{currentStageTitle || `阶段 ${currentStageId || 1}`}</Tag>
            <Tag style={{ borderRadius: 6 }}>共 {totalStages} 个阶段</Tag>
            <Tag style={{ borderRadius: 6 }}>任务 {completedTasks}/{totalTasks}</Tag>
            <Tag color="purple" style={{ borderRadius: 6 }}>掌握度 {masteryPercent}%</Tag>
          </Space>
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
            icon={<ReloadOutlined />}
            onClick={onRegenerate}
            style={{ borderRadius: 8 }}
          >
            重新生成路径
          </Button>
          <Button
            icon={<SwapOutlined />}
            onClick={() => navigate('/courses')}
            style={{ borderRadius: 8 }}
          >
            切换课程
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
