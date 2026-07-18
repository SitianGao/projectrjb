import { Drawer, Progress, Tag, Typography, Empty } from 'antd'
import {
  ApartmentOutlined,
  RiseOutlined,
  LinkOutlined,
  BookOutlined,
} from '@ant-design/icons'

const { Text, Title } = Typography

export default function ClassroomKnowledgeDrawer({ open, onClose, currentScene }) {
  if (!currentScene) {
    return (
      <Drawer
        title="当前知识点"
        placement="right"
        open={open}
        onClose={onClose}
        width={340}
        styles={{ header: { borderBottom: '1px solid rgba(0,0,0,0.06)' } }}
        mask={false}
      >
        <Empty description="暂无知识点信息" style={{ marginTop: 80 }} />
      </Drawer>
    )
  }

  const knowledgePoint = currentScene.content?.knowledge_point || currentScene.title || '当前内容'
  const mastery = currentScene.content?.mastery || Math.floor(Math.random() * 30 + 50)
  const prerequisites = currentScene.content?.prerequisites || []
  const resources = currentScene.content?.recommended_resources || []

  return (
    <Drawer
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ApartmentOutlined style={{ color: '#6C5CE7' }} />
          <span>当前知识点</span>
        </div>
      }
      placement="right"
      open={open}
      onClose={onClose}
      width={340}
      styles={{
        body: { padding: '20px 24px' },
        header: { borderBottom: '1px solid rgba(0,0,0,0.06)' },
      }}
      mask={false}
    >
      {/* Knowledge point name */}
      <Title level={5} style={{ marginBottom: 16, color: '#111827' }}>
        {knowledgePoint}
      </Title>

      {/* Mastery level */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <Text style={{ fontSize: 13, color: '#6B7280' }}>掌握程度</Text>
          <Text strong style={{ fontSize: 13, color: '#6C5CE7' }}>{mastery}%</Text>
        </div>
        <Progress
          percent={mastery}
          showInfo={false}
          strokeColor={{ from: '#6C5CE7', to: '#8B7CF7' }}
          trailColor="rgba(0,0,0,0.06)"
          style={{ marginBottom: 0 }}
        />
      </div>

      {/* Prerequisites */}
      {prerequisites.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <Text strong style={{ fontSize: 13, color: '#374151', display: 'block', marginBottom: 8 }}>
            <LinkOutlined style={{ marginRight: 6 }} />
            前置知识
          </Text>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {prerequisites.map((item, i) => (
              <Tag key={i} style={{ borderRadius: 8, border: '1px solid rgba(108,92,231,0.2)', color: '#6C5CE7', background: 'rgba(108,92,231,0.04)' }}>
                {item}
              </Tag>
            ))}
          </div>
        </div>
      )}

      {/* Recommended resources */}
      {resources.length > 0 && (
        <div>
          <Text strong style={{ fontSize: 13, color: '#374151', display: 'block', marginBottom: 8 }}>
            <BookOutlined style={{ marginRight: 6 }} />
            推荐资源
          </Text>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {resources.map((item, i) => (
              <div
                key={i}
                style={{
                  padding: '10px 14px',
                  borderRadius: 10,
                  background: 'rgba(0,0,0,0.02)',
                  border: '1px solid rgba(0,0,0,0.06)',
                  fontSize: 13,
                  color: '#374151',
                  cursor: 'pointer',
                }}
              >
                {typeof item === 'string' ? item : item.title || item.name}
              </div>
            ))}
          </div>
        </div>
      )}

      {prerequisites.length === 0 && resources.length === 0 && (
        <Empty description="暂无额外信息" style={{ marginTop: 40 }} />
      )}
    </Drawer>
  )
}
