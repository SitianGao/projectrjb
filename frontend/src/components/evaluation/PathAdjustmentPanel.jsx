import { Button, Card, Empty, List, Space, Tag, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'
import { adjustmentActionLabel, adjustmentStatusLabel } from '../../utils/evaluationLabels'

const { Text } = Typography

export default function PathAdjustmentPanel({ items = [], onViewPath, onApply, applying }) {
  const navigate = useNavigate()

  if (!items || items.length === 0) {
    return (
      <Card className="evaluation-card" title="学习路径调整">
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无路径调整" />
      </Card>
    )
  }

  return (
    <Card className="evaluation-card" title="学习路径调整">
      <List
        dataSource={items}
        renderItem={(item, index) => {
          const action = item.action || item.knowledge_point_name || ''
          const kp = item.knowledge_point || item.knowledgePoint || ''
          const status = item.status || 'suggested'
          const reason = item.reason || '根据评估诊断建议调整'
          return (
            <List.Item>
              <List.Item.Meta
                title={<Space>
                  <Tag color={
                    status === 'applied' ? 'green' :
                    status === 'failed' ? 'red' : 'blue'
                  }>{index + 1}</Tag>
                  <Text strong>{adjustmentActionLabel(action)}</Text>
                  {kp ? <Tag>{kp}</Tag> : null}
                  <Tag color={status === 'applied' ? 'green' : 'orange'}>
                    {adjustmentStatusLabel(status)}
                  </Tag>
                </Space>}
                description={reason}
              />
            </List.Item>
          )
        }}
      />
      <Space wrap style={{ marginTop: 12 }}>
        <Button type="primary" loading={applying} onClick={onApply}>
          应用建议并准备资源
        </Button>
        <Button onClick={() => onViewPath ? onViewPath() : navigate('/courses')}>
          查看调整后的学习路径
        </Button>
        <Button onClick={() => navigate('/assessment/tests')}>开始专项练习</Button>
      </Space>
    </Card>
  )
}
