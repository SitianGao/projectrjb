import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Empty, Result, Spin, Tag, Typography, Space } from 'antd'
import { ArrowLeftOutlined, ReloadOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { getResource } from '../api/resource'
import DocumentResourceViewer from '../components/DocumentResourceViewer'
import ExerciseResourceViewer from '../components/ExerciseResourceViewer'
import MindmapResourceViewer from '../components/MindmapResourceViewer'
import MarkdownRenderer from '../components/MarkdownRenderer'
import { normalizeTitle, getResourceStats } from '../utils/resourceNormalizer'

const { Title, Text } = Typography

const RENDERERS = {
  document: DocumentResourceViewer,
  exercise: ExerciseResourceViewer,
  quiz: ExerciseResourceViewer,
  mindmap: MindmapResourceViewer,
}

const TYPE_LABELS = {
  document: '讲义', exercise: '练习题', mindmap: '思维导图',
  ppt: 'PPT课件', code: '代码', reading: '阅读', audio: '音频',
}

export default function ResourceDetailPage() {
  const { resourceId } = useParams()
  const navigate = useNavigate()
  const [resource, setResource] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!resourceId) return
    setLoading(true)
    setError(null)
    getResource(resourceId)
      .then((data) => setResource(data))
      .catch((err) => setError(err.message || '加载失败'))
      .finally(() => setLoading(false))
  }, [resourceId])

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300, background: '#F6F7FB' }}><Spin size="large" /></div>
  }

  if (error || !resource) {
    return (
      <div style={{ maxWidth: 500, margin: '60px auto', padding: 24 }}>
        <Result status="error" title="资源加载失败" subTitle={error || '资源不存在'}
          extra={<Button type="primary" icon={<ReloadOutlined />} onClick={() => window.location.reload()}>重试</Button>} />
      </div>
    )
  }

  const title = normalizeTitle(resource.title, resource.type, resource.topic)
  const Renderer = RENDERERS[resource.type]
  const stats = getResourceStats(resource)
  const typeLabel = TYPE_LABELS[resource.type] || '资源'

  return (
    <div style={{ minHeight: '100%', background: '#F6F7FB', padding: '20px 24px 48px' }}>
      <div style={{ maxWidth: 960, margin: '0 auto' }}>
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/resources')} style={{ marginBottom: 16, paddingLeft: 0 }}>
          返回资源中心
        </Button>

        {/* Resource header */}
        <div style={{ background: '#FFFFFF', borderRadius: 16, padding: '20px 28px', border: '1px solid #E5E7EB', marginBottom: 24 }}>
          <Space size={8} wrap style={{ marginBottom: 8 }}>
            <Tag color="purple" style={{ borderRadius: 6 }}>{typeLabel}</Tag>
            {resource.difficulty && <Tag style={{ borderRadius: 6 }}>{resource.difficulty}</Tag>}
            {resource.stage_id && <Tag style={{ borderRadius: 6 }}>阶段{resource.stage_id}</Tag>}
          </Space>
          <Title level={3} style={{ margin: '8px 0', color: '#111827' }}>{title}</Title>
          <Space size={16}>
            {stats && <Text style={{ fontSize: 13, color: '#6B7280' }}>{stats.icon} {stats.label}</Text>}
            {resource.estimated_minutes && <Text style={{ fontSize: 13, color: '#6B7280' }}><ClockCircleOutlined /> {resource.estimated_minutes} 分钟</Text>}
            {resource.topic && <Text style={{ fontSize: 13, color: '#6B7280' }}>主题：{resource.topic}</Text>}
          </Space>
        </div>

        {/* Resource content */}
        <div style={{ background: '#FFFFFF', borderRadius: 16, padding: '24px 28px', border: '1px solid #E5E7EB' }}>
          {Renderer ? <Renderer resource={resource} /> : resource.content ? (
            typeof resource.content === 'string' ? <MarkdownRenderer content={resource.content} /> : <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>{JSON.stringify(resource.content, null, 2)}</pre>
          ) : (
            <Empty description="该资源暂无内容" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </div>
      </div>
    </div>
  )
}
