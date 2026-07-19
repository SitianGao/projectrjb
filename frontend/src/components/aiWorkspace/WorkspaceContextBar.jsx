import { Typography } from 'antd'
import { LinkOutlined } from '@ant-design/icons'

const { Text } = Typography

export default function WorkspaceContextBar({ course, currentStage, currentTask, onViewTask }) {
  return (
    <div className="workspace-context-bar">
      <div className="context-bar-chain">
        <Text strong>{course?.title || '当前课程'}</Text>
        {currentStage?.title && (
          <>
            <Text type="secondary">/</Text>
            <Text>{currentStage.title}</Text>
          </>
        )}
      </div>
      <div className="context-bar-meta">
        {currentTask?.title && (
          <Text type="secondary" style={{ fontSize: 13 }}>
            当前任务：{currentTask.title}
          </Text>
        )}
      </div>
      {onViewTask && currentTask?.task_id && (
        <a className="context-bar-link" onClick={onViewTask}>
          <LinkOutlined /> 查看当前任务
        </a>
      )}
    </div>
  )
}
