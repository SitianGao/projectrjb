import { Button, Card, Space } from 'antd'
import { ArrowLeftOutlined, ArrowRightOutlined, CheckCircleOutlined } from '@ant-design/icons'

export default function ClassroomActionFooter({
  isFirst,
  isLast,
  completing,
  onPrev,
  onCompleteScene,
  onCompleteClassroom,
}) {
  return (
    <Card className="classroom-action-footer">
      <Space>
        <Button icon={<ArrowLeftOutlined />} disabled={isFirst} onClick={onPrev}>上一步</Button>
        {isLast ? (
          <Button type="primary" icon={<CheckCircleOutlined />} loading={completing} onClick={onCompleteClassroom}>
            完成课堂并生成学习记录
          </Button>
        ) : (
          <Button type="primary" icon={<ArrowRightOutlined />} onClick={onCompleteScene}>
            完成并进入下一场景
          </Button>
        )}
      </Space>
    </Card>
  )
}
