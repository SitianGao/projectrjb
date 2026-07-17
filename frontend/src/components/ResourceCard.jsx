import { Card, Tag, Typography, Space } from 'antd'
import {
  FileTextOutlined, QuestionCircleOutlined, BranchesOutlined,
  CodeOutlined, EditOutlined, ClockCircleOutlined, BookOutlined,
  SoundOutlined, FilePptOutlined,
} from '@ant-design/icons'
import { formatRelativeTime } from '../utils/format'
import { normalizeTitle, getResourceStats } from '../utils/resourceNormalizer'

const { Text, Paragraph, Title } = Typography

const typeConfig = {
  document: { icon: <FileTextOutlined />, color: 'blue', label: '讲义' },
  quiz: { icon: <QuestionCircleOutlined />, color: 'orange', label: '练习题' },
  mindmap: { icon: <BranchesOutlined />, color: 'purple', label: '思维导图' },
  exercise: { icon: <EditOutlined />, color: 'green', label: '练习题' },
  code: { icon: <CodeOutlined />, color: 'red', label: '代码' },
  ppt: { icon: <FilePptOutlined />, color: 'magenta', label: 'PPT' },
  audio: { icon: <SoundOutlined />, color: 'geekblue', label: '音频' },
  reading: { icon: <BookOutlined />, color: 'cyan', label: '阅读' },
}

/**
 * Resource card — shows only summary + stats, never raw JSON/Markdown content.
 */
export default function ResourceCard({ resource, onClick, loading = false }) {
  if (loading) return <Card loading style={{ borderRadius: 12, border: '1px solid var(--border)' }} />
  if (!resource) return <Card style={{ borderRadius: 12 }}><Text type="secondary">资源不可用</Text></Card>

  const config = typeConfig[resource.type] || typeConfig.document
  const title = normalizeTitle(resource.title, resource.type, resource.topic)
  const stats = getResourceStats(resource)
  const summary = resource.summary || resource.description || ''

  return (
    <Card hoverable className="resource-card"
      style={{ height: '100%', borderRadius: 12, border: '1px solid var(--border)', transition: 'box-shadow 0.25s, transform 0.25s' }}
      styles={{ body: { padding: '18px 20px', display: 'flex', flexDirection: 'column', height: '100%' } }}
      onClick={() => onClick?.(resource)}>
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Tag icon={config.icon} color={config.color} style={{ borderRadius: 6, fontSize: 12 }}>{config.label}</Tag>
          {resource.difficulty && <Tag style={{ borderRadius: 6, fontSize: 11 }}>{resource.difficulty}</Tag>}
        </div>
        <Title level={5} style={{ margin: 0, lineHeight: 1.4, fontSize: 15 }}>{title}</Title>
        {stats && <Text type="secondary" style={{ fontSize: 11 }}>{stats.icon} {stats.label}</Text>}
        {summary && (
          <Paragraph type="secondary" style={{ marginBottom: 0, flex: 1, fontSize: 12, lineHeight: 1.5 }}
            ellipsis={{ rows: 2 }}>
            {summary}
          </Paragraph>
        )}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto' }}>
          <Space size={4} wrap>
            {resource.stage_id && <Tag style={{ borderRadius: 4, fontSize: 11 }}>阶段{resource.stage_id}</Tag>}
          </Space>
          <Text type="secondary" style={{ fontSize: 11, whiteSpace: 'nowrap' }}>
            <ClockCircleOutlined style={{ marginRight: 3 }} />{formatRelativeTime(resource.createdAt)}
          </Text>
        </div>
      </div>
    </Card>
  )
}
