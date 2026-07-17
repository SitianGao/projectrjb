import { Button, Card, Empty, List, Space, Tag, Typography } from 'antd'

const { Paragraph, Text } = Typography

export default function PathAdjustmentPanel({ items = [], onAccept, onPreview, loading }) {
  return (
    <Card className="evaluation-card" title="学习路径调整建议">
      {items.length ? (
        <>
          <Paragraph>根据本次评估，系统建议先确认以下路径调整，再由 PlannerAgent 生成路径变更草案。</Paragraph>
          <List
            dataSource={items}
            renderItem={(item, index) => (
              <List.Item>
                <List.Item.Meta
                  title={<><Tag color="purple">{index + 1}</Tag>{item.knowledge_point_name || item.knowledge_point_id}</>}
                  description={item.reason}
                />
                <Text type="secondary">预计提升 {item.estimated_score_after?.join('～') || '--'} 分</Text>
              </List.Item>
            )}
          />
          <Space wrap>
            <Button type="primary" onClick={onAccept} loading={loading}>接受调整</Button>
            <Button onClick={onPreview} loading={loading}>查看详情</Button>
            <Button>暂不调整</Button>
          </Space>
        </>
      ) : (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无路径调整建议" />
      )}
    </Card>
  )
}
