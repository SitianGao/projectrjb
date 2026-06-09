import { Card, Tag, Typography, Button, Space } from 'antd'
import {
  FileTextOutlined,
  QuestionCircleOutlined,
  BranchesOutlined,
  DownloadOutlined,
  EyeOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { formatDate, formatRelativeTime, truncateText } from '../utils/format'

const { Text, Paragraph, Title } = Typography

const typeConfig = {
  document: { icon: <FileTextOutlined />, color: 'blue', label: '文档' },
  quiz: { icon: <QuestionCircleOutlined />, color: 'orange', label: '练习题' },
  mindmap: { icon: <BranchesOutlined />, color: 'purple', label: '思维导图' },
}

/**
 * 学习资源卡片
 *
 * @param {Object} props
 * @param {Object} props.resource - 资源数据
 * @param {string} props.resource.id
 * @param {'document'|'quiz'|'mindmap'} props.resource.type
 * @param {string} props.resource.title
 * @param {string} props.resource.description
 * @param {Array<string>} props.resource.tags
 * @param {string} props.resource.createdAt
 * @param {Function} props.onClick - 点击查看
 * @param {Function} props.onDownload - 下载
 * @param {boolean} props.loading
 */
export default function ResourceCard({ resource, onClick, onDownload, loading = false }) {
  if (loading) {
    return <Card loading />
  }

  if (!resource) {
    return (
      <Card>
        <Text type="secondary">资源不可用</Text>
      </Card>
    )
  }

  const config = typeConfig[resource.type] || typeConfig.document

  return (
    <Card
      hoverable
      style={{ height: '100%' }}
      onClick={() => onClick?.(resource)}
      actions={[
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={(e) => {
            e.stopPropagation()
            onClick?.(resource)
          }}
        >
          查看
        </Button>,
        <Button
          type="link"
          icon={<DownloadOutlined />}
          onClick={(e) => {
            e.stopPropagation()
            onDownload?.(resource)
          }}
        >
          下载
        </Button>,
      ]}
    >
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {/* 类型标签 + 标题 */}
        <Space>
          <Tag icon={config.icon} color={config.color}>
            {config.label}
          </Tag>
        </Space>
        <Title level={5} style={{ margin: 0 }}>
          {resource.title || '未命名资源'}
        </Title>

        {/* 描述 */}
        <Paragraph type="secondary" style={{ marginBottom: 8 }}>
          {truncateText(resource.description, 120)}
        </Paragraph>

        {/* 标签 */}
        {resource.tags?.length > 0 && (
          <div>
            {resource.tags.map((tag) => (
              <Tag key={tag}>{tag}</Tag>
            ))}
          </div>
        )}

        {/* 时间 */}
        <Text type="secondary" style={{ fontSize: 12 }}>
          <ClockCircleOutlined style={{ marginRight: 4 }} />
          {formatRelativeTime(resource.createdAt)}
        </Text>
      </Space>
    </Card>
  )
}
