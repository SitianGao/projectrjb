import { Card, Tag, Typography, Button, Space, Tooltip } from 'antd'
import {
  FileTextOutlined,
  QuestionCircleOutlined,
  BranchesOutlined,
  CodeOutlined,
  EditOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  ExpandOutlined,
} from '@ant-design/icons'
import MarkdownRenderer from './MarkdownRenderer'
import { formatDate, formatRelativeTime, truncateText } from '../utils/format'

const { Text, Paragraph, Title } = Typography

const typeConfig = {
  document: { icon: <FileTextOutlined />, color: 'blue', label: '文档' },
  quiz: { icon: <QuestionCircleOutlined />, color: 'orange', label: '练习题' },
  mindmap: { icon: <BranchesOutlined />, color: 'purple', label: '思维导图' },
  exercise: { icon: <EditOutlined />, color: 'green', label: '练习题' },
  code: { icon: <CodeOutlined />, color: 'red', label: '代码' },
}

/**
 * 学习资源卡片
 */
export default function ResourceCard({ resource, onClick, onDownload, loading = false, showContent = false }) {
  if (loading) {
    return <Card loading style={{ borderRadius: 12, border: '1px solid var(--border)' }} />
  }

  if (!resource) {
    return (
      <Card style={{ borderRadius: 12 }}>
        <Text type="secondary">资源不可用</Text>
      </Card>
    )
  }

  const config = typeConfig[resource.type] || typeConfig.document

  return (
    <Card
      hoverable
      className="resource-card"
      style={{
        height: '100%',
        borderRadius: 12,
        border: '1px solid var(--border)',
        transition: 'box-shadow 0.25s, transform 0.25s',
      }}
      styles={{ body: { padding: '20px 22px', display: 'flex', flexDirection: 'column', height: '100%' } }}
      onClick={() => onClick?.(resource)}
    >
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: 12 }}>
        {/* 头部：类型标签 + 展开图标 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Tag icon={config.icon} color={config.color} style={{ borderRadius: 6, padding: '2px 10px', fontSize: 13 }}>
            {config.label}
          </Tag>
          {showContent && (
            <Tooltip title="点击查看详情">
              <ExpandOutlined
                style={{ color: 'var(--text-muted)', cursor: 'pointer', fontSize: 15 }}
                onClick={(e) => {
                  e.stopPropagation()
                  onClick?.(resource)
                }}
              />
            </Tooltip>
          )}
        </div>

        {/* 标题 */}
        <Title level={5} style={{ margin: 0, lineHeight: 1.4, fontSize: 16 }}>
          {resource.title || '未命名资源'}
        </Title>

        {/* 描述 或 Markdown 内容 */}
        {showContent && resource.content ? (
          <div
            style={{
              flex: 1,
              maxHeight: 300,
              overflow: 'auto',
              padding: '8px 0',
              borderTop: '1px solid var(--border)',
              borderBottom: '1px solid var(--border)',
            }}
          >
            <MarkdownRenderer content={resource.content} compact />
          </div>
        ) : (
          <Paragraph type="secondary" style={{ marginBottom: 8, flex: 1 }}>
            {truncateText(resource.description, 120)}
          </Paragraph>
        )}

        {/* 底部信息 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto' }}>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {resource.tags?.map((tag) => (
              <Tag key={tag} style={{ borderRadius: 4, fontSize: 12 }}>{tag}</Tag>
            ))}
          </div>
          <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
            <ClockCircleOutlined style={{ marginRight: 4 }} />
            {formatRelativeTime(resource.createdAt)}
          </Text>
        </div>
      </div>
    </Card>
  )
}
