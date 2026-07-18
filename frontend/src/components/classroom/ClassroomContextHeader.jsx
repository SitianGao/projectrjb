import { Breadcrumb, Button, Card, Space, Tag, Typography } from 'antd'
import { ArrowLeftOutlined, ExpandOutlined, SaveOutlined, AimOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

export default function ClassroomContextHeader({ classroom, currentIndex, onBack }) {
  const total = classroom?.scenes?.length || 0
  return (
    <Card className="classroom-header">
      <div className="classroom-header-top">
        <Breadcrumb items={[
          { title: '学习路径' },
          { title: classroom?.generation_brief?.course_name || '人工智能与深度学习' },
          { title: '阶段二' },
          { title: '互动课堂' },
        ]} />
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回阶段详情</Button>
          <Button icon={<AimOutlined />}>查看学习目标</Button>
          <Button icon={<SaveOutlined />}>保存并退出</Button>
          <Button type="primary" icon={<ExpandOutlined />}>全屏课堂</Button>
        </Space>
      </div>
      <div className="classroom-header-main">
        <div>
          <Tag color="purple">学习中</Tag>
          <Title level={3}>{classroom?.title || '梯度下降与学习率沉浸式课堂'}</Title>
          <Text type="secondary">{total} 个课堂场景 · 预计 {classroom?.estimated_minutes || 25} 分钟 · 当前进度 {Math.min(currentIndex + 1, total)} / {total}</Text>
        </div>
      </div>
    </Card>
  )
}
