import { Button, Card, Empty, Progress, Typography } from 'antd'
import { BranchesOutlined } from '@ant-design/icons'

const { Text } = Typography

export default function CourseProgressOverview({ progress, onGeneratePath }) {
  const stages = progress?.stages || []
  return (
    <Card className="evaluation-card" title="学习进度总览">
      {stages.length ? (
        <>
          <div className="course-progress-summary">
            <Text>当前阶段：{progress.current_stage || '--'}</Text>
            <Text>课程整体进度：{progress.overall_percent || 0}%</Text>
            <Text>已完成任务：{progress.completed_tasks || 0}</Text>
            <Text>剩余任务：{progress.remaining_tasks || 0}</Text>
          </div>
          <div className="stage-progress-list">
            {stages.map((stage) => (
              <div className="stage-progress-row" key={stage.stage_id}>
                <div>
                  <Text strong>{stage.title}</Text>
                  <Text type="secondary">{stage.locked ? '未解锁' : `任务 ${stage.completed_tasks}/${stage.total_tasks}`}</Text>
                </div>
                <Progress percent={stage.locked ? 0 : stage.percent} strokeColor={stage.is_current ? '#6C5CE7' : '#22C55E'} />
              </div>
            ))}
          </div>
        </>
      ) : (
        <Empty description="暂未生成学习路径">
          <Button type="primary" icon={<BranchesOutlined />} onClick={onGeneratePath}>生成学习路径</Button>
        </Empty>
      )}
    </Card>
  )
}
