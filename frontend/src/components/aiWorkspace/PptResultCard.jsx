import { Card, Progress, Typography, Button, Space, Tag, Descriptions } from 'antd'
import { FilePptOutlined, DownloadOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { getPptDownloadUrl } from '../../api/resource'

const { Text, Title } = Typography

export default function PptResultCard({ resource }) {
  if (!resource) return null

  const content = typeof resource.content === 'string'
    ? (() => { try { return JSON.parse(resource.content) } catch { return {} } })()
    : (resource.content || {})

  const outline = content.outline || []
  const fileName = content.file_name || ''
  const fileSize = content.file_size || 0
  const generatedAt = content.generated_at || resource.created_at

  // 格式化文件大小
  function formatSize(bytes) {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <Card
      title={
        <Space>
          <FilePptOutlined style={{ color: '#FF6B6B' }} />
          <span>PPT 课件已生成</span>
          <Tag color="success" icon={<CheckCircleOutlined />}>完成</Tag>
        </Space>
      }
      style={{ borderRadius: 14 }}
    >
      <Descriptions column={1} size="small" style={{ marginBottom: 16 }}>
        <Descriptions.Item label="主题">{resource.topic || resource.title}</Descriptions.Item>
        <Descriptions.Item label="难度">{resource.difficulty || '中级'}</Descriptions.Item>
        {fileName && <Descriptions.Item label="文件名">{fileName}</Descriptions.Item>}
        {fileSize > 0 && <Descriptions.Item label="文件大小">{formatSize(fileSize)}</Descriptions.Item>}
        {generatedAt && <Descriptions.Item label="生成时间">{new Date(generatedAt).toLocaleString('zh-CN')}</Descriptions.Item>}
        {outline.length > 0 && <Descriptions.Item label="章节数">{outline.length} 章</Descriptions.Item>}
      </Descriptions>

      {/* 大纲预览 */}
      {outline.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Text strong style={{ display: 'block', marginBottom: 8 }}>📋 大纲预览</Text>
          <div style={{ maxHeight: 300, overflow: 'auto', padding: '12px', background: '#F9F9F9', borderRadius: 8 }}>
            {outline.map((chapter, i) => (
              <div key={i} style={{ marginBottom: 12 }}>
                <Text strong style={{ fontSize: 13 }}>
                  {i + 1}. {chapter.title}
                </Text>
                {chapter.subtitles?.length > 0 && (
                  <ul style={{ margin: '4px 0 0 20px', padding: 0 }}>
                    {chapter.subtitles.map((sub, j) => (
                      <li key={j} style={{ fontSize: 12, color: '#666', lineHeight: 1.8 }}>
                        {sub.title}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 下载按钮 */}
      <Space>
        {resource.artifact_url ? (
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            href={getPptDownloadUrl(resource.id)}
            target="_blank"
            style={{ background: '#FF6B6B', borderColor: '#FF6B6B' }}
          >
            下载 PPT 文件
          </Button>
        ) : (
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            disabled
          >
            下载链接不可用
          </Button>
        )}
      </Space>
    </Card>
  )
}
