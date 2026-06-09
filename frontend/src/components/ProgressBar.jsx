import { Progress, Space, Typography, Steps, Tag } from 'antd'
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'

const { Text } = Typography

/**
 * 生成进度条组件
 *
 * 用于展示 AI 生成任务（生成路径/资源/评估）的实时进度。
 *
 * @param {Object} props
 * @param {string} props.status - 'idle' | 'pending' | 'running' | 'completed' | 'failed'
 * @param {number} props.percent - 进度百分比 0-100
 * @param {Array<{key: string, label: string, status: 'wait'|'process'|'finish'|'error'}>} props.steps
 * @param {string} props.message - 当前阶段描述
 * @param {string} props.error - 错误信息
 */
export default function ProgressBar({
  status = 'idle',
  percent = 0,
  steps = [],
  message = '',
  error = '',
}) {
  const statusConfig = {
    idle: { color: 'default', icon: <ClockCircleOutlined />, label: '等待开始' },
    pending: { color: 'default', icon: <ClockCircleOutlined />, label: '排队中' },
    running: { color: 'active', icon: <LoadingOutlined />, label: '生成中' },
    completed: { color: 'success', icon: <CheckCircleOutlined />, label: '已完成' },
    failed: { color: 'exception', icon: <CloseCircleOutlined />, label: '失败' },
  }

  const current = statusConfig[status] || statusConfig.idle

  return (
    <div style={{ padding: '16px 0' }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 状态标签 + 百分比 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Tag
              color={current.color === 'exception' ? 'error' : current.color === 'success' ? 'success' : 'processing'}
              icon={current.icon}
            >
              {current.label}
            </Tag>
            {message && <Text type="secondary">{message}</Text>}
          </Space>
          {status === 'completed' ? (
            <Text type="success">
              <CheckCircleOutlined /> 100%
            </Text>
          ) : status === 'failed' ? (
            <Text type="danger">
              <CloseCircleOutlined /> 失败
            </Text>
          ) : (
            <Text type="secondary">{percent}%</Text>
          )}
        </div>

        {/* 进度条 */}
        <Progress
          percent={percent}
          status={status === 'failed' ? 'exception' : status === 'completed' ? 'success' : 'active'}
          showInfo={false}
          strokeColor={status === 'failed' ? '#ff4d4f' : '#1677ff'}
        />

        {/* 子步骤 */}
        {steps.length > 0 && (
          <Steps
            size="small"
            current={steps.filter((s) => s.status === 'finish').length}
            items={steps.map((s) => ({
              title: s.label,
              status: s.status,
            }))}
          />
        )}

        {/* 错误信息 */}
        {error && (
          <Text type="danger" style={{ whiteSpace: 'pre-wrap' }}>
            错误详情: {error}
          </Text>
        )}
      </Space>
    </div>
  )
}
