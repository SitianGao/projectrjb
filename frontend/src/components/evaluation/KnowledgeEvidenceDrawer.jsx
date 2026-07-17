import { Button, Descriptions, Drawer, List, Space, Typography } from 'antd'

const { Text } = Typography

export default function KnowledgeEvidenceDrawer({ open, item, onClose }) {
  return (
    <Drawer title={item?.name || '诊断依据'} open={open} onClose={onClose} width={520}>
      {item && (
        <Space direction="vertical" size={18} style={{ width: '100%' }}>
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="掌握度">{item.score}%</Descriptions.Item>
            <Descriptions.Item label="优先级">{item.priority || '优势知识点'}</Descriptions.Item>
            <Descriptions.Item label="证据数量">{item.evidence_count || item.evidence?.length || 0}</Descriptions.Item>
            <Descriptions.Item label="评估置信度">{Math.round((item.confidence || 0) * 100)}%</Descriptions.Item>
          </Descriptions>
          <div>
            <Text strong>诊断依据</Text>
            <List dataSource={item.evidence || []} renderItem={(evidence) => <List.Item>{evidence}</List.Item>} />
          </div>
          {item.wrong_questions?.length > 0 && (
            <div>
              <Text strong>相关错题</Text>
              <List
                dataSource={item.wrong_questions}
                renderItem={(row) => (
                  <List.Item>
                    <Text>{row.question}</Text>
                    <Text type="secondary">错误 {row.wrong_count} 次</Text>
                  </List.Item>
                )}
              />
            </div>
          )}
          <Space wrap>
            <Button type="primary">开始专项练习</Button>
            <Button>查看推荐资源</Button>
            <Button>加入复习计划</Button>
          </Space>
        </Space>
      )}
    </Drawer>
  )
}
