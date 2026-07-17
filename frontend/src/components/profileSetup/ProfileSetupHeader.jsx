import { Breadcrumb, Button, Card, Steps, Typography } from 'antd'
import { ArrowLeftOutlined, BranchesOutlined, HomeOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

export default function ProfileSetupHeader({ course, mode, completion = 0, onBack, onPath }) {
  const step = completion >= 0.85 ? 1 : 0
  return (
    <Card className="profile-setup-header">
      <div className="profile-header-top">
        <Breadcrumb
          items={[
            { title: <span><HomeOutlined /> 学习首页</span> },
            { title: course?.title || '课程画像' },
            { title: mode === 'update' ? '更新画像' : '画像初始化' },
          ]}
        />
        <div className="profile-header-actions">
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回学习首页</Button>
          <Button icon={<BranchesOutlined />} onClick={onPath}>查看学习路径</Button>
        </div>
      </div>
      <div className="profile-header-main">
        <div>
          <Text className="profile-kicker">Course Profile Setup</Text>
          <Title level={2}>{course?.title || '课程画像初始化'}</Title>
          <Text type="secondary">ChatBox 只用于建立或更新这门课的学习画像；确认后再生成学习路径。</Text>
        </div>
        <Steps
          current={step}
          items={[
            { title: '对话采集' },
            { title: '确认画像' },
            { title: '生成路径' },
          ]}
          className="profile-header-steps"
        />
      </div>
    </Card>
  )
}
