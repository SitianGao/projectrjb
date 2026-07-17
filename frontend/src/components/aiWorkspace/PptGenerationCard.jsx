import { Button, Card, Space, Typography } from 'antd'
import { FilePptOutlined } from '@ant-design/icons'

const { Text } = Typography

export default function PptGenerationCard({ onGenerate, loading }) {
  return (
    <Card className="workspace-tool-card" title="PPT 课件生成">
      <Text type="secondary">按当前阶段主题生成可复习的 PPT 课件。</Text>
      <Space wrap>
        <Button icon={<FilePptOutlined />} loading={loading} onClick={() => onGenerate?.(['ppt'])}>
          生成 PPT
        </Button>
      </Space>
    </Card>
  )
}
