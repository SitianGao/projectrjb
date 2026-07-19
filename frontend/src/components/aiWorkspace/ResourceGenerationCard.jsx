import { Button, Card, Space, Typography } from 'antd'
import { FileTextOutlined } from '@ant-design/icons'

const { Text } = Typography

export default function ResourceGenerationCard({ onGenerate, loading }) {
  return (
    <Card className="workspace-tool-card" title="资源生成">
      <Text type="secondary">基于当前课程上下文生成讲义、练习和拓展材料。</Text>
      <Space wrap>
        <Button icon={<FileTextOutlined />} loading={loading} onClick={() => onGenerate?.(['document', 'exercise'])}>
          生成讲义和练习
        </Button>
      </Space>
    </Card>
  )
}
