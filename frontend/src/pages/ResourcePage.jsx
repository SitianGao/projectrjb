import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Typography, Input, Select, Button, Empty, Row, Col, Space, Tabs,
  Tag, Card, Skeleton, Result, Dropdown, message, Modal,
} from 'antd'
import {
  SearchOutlined, ThunderboltOutlined, FileTextOutlined,
  EditOutlined, CodeOutlined, FilePptOutlined, SoundOutlined,
  BranchesOutlined, DownloadOutlined, StarOutlined, StarFilled,
  MoreOutlined, ClockCircleOutlined, CheckCircleOutlined,
  BookOutlined, ReloadOutlined, FilterOutlined, InboxOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'
import MarkdownRenderer from '../components/MarkdownRenderer'
import ResourceGenerateDrawer from '../components/ResourceGenerateDrawer'
import { useResources } from '../hooks/useResources'
import { useAuth } from '../contexts/AuthContext'
import { normalizeTitle, getResourceStats } from '../utils/resourceNormalizer'

const { Text, Title, Paragraph } = Typography

const TYPE_CONFIG = {
  document: { icon: <FileTextOutlined />, color: 'blue', label: '讲义' },
  exercise: { icon: <EditOutlined />, color: 'green', label: '练习题' },
  code: { icon: <CodeOutlined />, color: 'red', label: '代码' },
  mindmap: { icon: <BranchesOutlined />, color: 'purple', label: '思维导图' },
  ppt: { icon: <FilePptOutlined />, color: 'magenta', label: 'PPT' },
  audio: { icon: <SoundOutlined />, color: 'geekblue', label: '音频' },
  interactive_classroom: { icon: <ExperimentOutlined />, color: 'purple', label: 'AI 互动课堂' },
  reading: { icon: <BookOutlined />, color: 'cyan', label: '阅读' },
}

const DIFFICULTY_COLORS = { '初级': 'green', '中级': 'orange', '高级': 'red' }

export default function ResourcePage() {
  const navigate = useNavigate()
  const { courses, activeCourse } = useAuth()

  // ── Filters ──
  const [keyword, setKeyword] = useState('')
  const [filterCourse, setFilterCourse] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterDifficulty, setFilterDifficulty] = useState('')
  const [sortBy, setSortBy] = useState('recent')
  const [activeTab, setActiveTab] = useState('all')

  // ── Generate drawer ──
  const [genDrawerOpen, setGenDrawerOpen] = useState(false)
  const [genContext, setGenContext] = useState({ source: 'global' })

  // ── Favorites ──
  const [favorites, setFavorites] = useState(new Set())

  // ── Data ──
  const { data: resources, total, loading, error, reload } = useResources({
    courseId: filterCourse || undefined,
    type: filterType || undefined,
    difficulty: filterDifficulty || undefined,
    keyword: keyword || undefined,
    sort: sortBy,
  })

  const filtered = useMemo(() => {
    let list = resources
    if (activeTab === 'recent') {
      list = list.slice(0, 5)
    } else if (activeTab === 'favorites') {
      list = list.filter((r) => favorites.has(r.id))
    }
    return list
  }, [resources, activeTab, favorites])

  const tabItems = [
    { key: 'all', label: `全部资源 ${total}` },
    { key: 'recent', label: '最近生成' },
    { key: 'favorites', label: `我的收藏 ${favorites.size}` },
  ]

  const toggleFavorite = (id) => {
    setFavorites((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const openResource = (resource) => {
    if (resource.type === 'interactive_classroom') {
      const classroomId = resource.classroom_id || resource.classroomId
      const courseId = resource.course_id || activeCourse?.id
      if (classroomId && courseId) {
        navigate(`/course/${courseId}/classroom/${classroomId}`)
        return
      }
      if (courseId) {
        navigate(`/course/${courseId}/learn/task_gradient_classroom`)
        return
      }
    }
    navigate(`/resources/${resource.id}`)
  }

  return (
    <div style={{ minHeight: '100%', background: '#F6F7FB', padding: '20px 24px 48px' }}>
      <div style={{ maxWidth: 1440, margin: '0 auto' }}>

        {/* ── Header ── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
          <div>
            <Title level={3} style={{ margin: 0, color: '#111827' }}>资源中心</Title>
            <Text style={{ color: '#6B7280', fontSize: 14 }}>
              生成、管理并复用你的个性化学习资源
            </Text>
          </div>
          <Button type="primary" size="large" icon={<ThunderboltOutlined />}
            onClick={() => { setGenContext({ source: 'global' }); setGenDrawerOpen(true) }}
            style={{ borderRadius: 10, background: '#6C5CE7', borderColor: '#6C5CE7' }}>
            生成新资源
          </Button>
        </div>

        {/* ── Filter bar ── */}
        <Card style={{ borderRadius: 16, marginBottom: 20, border: '1px solid #E5E7EB' }}
          styles={{ body: { padding: '14px 20px' } }}>
          <Space size={12} wrap style={{ width: '100%' }}>
            <Input prefix={<SearchOutlined style={{ color: '#6C5CE7' }} />}
              placeholder="搜索资源名称、主题、知识点"
              value={keyword} onChange={(e) => setKeyword(e.target.value)}
              style={{ width: 260, borderRadius: 8 }} allowClear />
            <Select placeholder="全部课程" value={filterCourse} onChange={setFilterCourse}
              allowClear style={{ width: 140, borderRadius: 8 }}
              options={(courses || []).map((c) => ({ label: c.title, value: c.id }))} />
            <Select placeholder="全部类型" value={filterType} onChange={setFilterType}
              allowClear style={{ width: 120, borderRadius: 8 }}
              options={Object.entries(TYPE_CONFIG).map(([k, v]) => ({ label: v.label, value: k }))} />
            <Select placeholder="全部难度" value={filterDifficulty} onChange={setFilterDifficulty}
              allowClear style={{ width: 110, borderRadius: 8 }}
              options={[{ label: '初级', value: '初级' }, { label: '中级', value: '中级' }, { label: '高级', value: '高级' }]} />
            <Select value={sortBy} onChange={setSortBy} style={{ width: 130, borderRadius: 8 }}
              options={[
                { label: '最近生成', value: 'recent' },
                { label: '最近使用', value: 'used' },
                { label: '最多访问', value: 'views' },
                { label: '名称排序', value: 'name' },
              ]} />
            <Button icon={<ReloadOutlined />} onClick={reload} style={{ borderRadius: 8 }} />
          </Space>
        </Card>

        {/* ── Tabs ── */}
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems}
          style={{ marginBottom: 16 }} />

        {/* ── Content ── */}
        {loading ? (
          <Skeleton active paragraph={{ rows: 4 }} />
        ) : error ? (
          <Result status="error" title="资源加载失败" subTitle={error}
            extra={<Button type="primary" icon={<ReloadOutlined />} onClick={reload}>重试</Button>} />
        ) : filtered.length === 0 ? (
          <Card style={{ borderRadius: 16, textAlign: 'center', padding: 48, border: '1px solid #E5E7EB' }}>
            <InboxOutlined style={{ fontSize: 48, color: '#D1D5DB', marginBottom: 16 }} />
            <Title level={4} style={{ color: '#111827' }}>还没有学习资源</Title>
            <Paragraph style={{ color: '#6B7280', maxWidth: 460, margin: '0 auto 20px' }}>
              你可以选择一门课程和学习主题，生成讲义、练习题、PPT 或思维导图。
              生成的资源会自动保存到此处，并可关联到具体课程和阶段。
            </Paragraph>
            <Button type="primary" size="large" icon={<ThunderboltOutlined />}
              onClick={() => { setGenContext({ source: 'global' }); setGenDrawerOpen(true) }}
              style={{ borderRadius: 8, background: '#6C5CE7' }}>
              生成第一个资源
            </Button>
          </Card>
        ) : (
          <Row gutter={[16, 16]}>
            {filtered.map((res) => {
              const cfg = TYPE_CONFIG[res.type] || TYPE_CONFIG.document
              const isFav = favorites.has(res.id)
              return (
                <Col xs={24} sm={12} lg={8} xl={6} key={res.id}>
                  <Card
                    hoverable
                    style={{ borderRadius: 12, border: '1px solid #E5E7EB', height: '100%', minWidth: 0 }}
                    styles={{ body: { padding: '16px 18px' } }}
                    onClick={() => openResource(res)}
                  >
                    {/* Type + difficulty */}
                    <Space size={4} style={{ marginBottom: 8 }}>
                      <Tag icon={cfg.icon} color={cfg.color} style={{ borderRadius: 6, margin: 0 }}>{cfg.label}</Tag>
                      {res.difficulty && <Tag color={DIFFICULTY_COLORS[res.difficulty] || 'default'} style={{ borderRadius: 6, margin: 0 }}>{res.difficulty}</Tag>}
                      {res.stage_id && <Tag style={{ borderRadius: 6, margin: 0 }}>阶段{res.stage_id}</Tag>}
                    </Space>

                    {/* Title */}
                    <Text strong style={{ fontSize: 14, color: '#111827', display: 'block', marginBottom: 6 }}
                      ellipsis={{ rows: 2 }}>{normalizeTitle(res.title, res.type, res.topic)}</Text>
                    {/* Stats */}
                    {(() => { const s = getResourceStats(res); return s ? <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 6 }}>{s.icon} {s.label}</Text> : null })()}

                    {/* Summary */}
                    {res.description && (
                      <Paragraph type="secondary" style={{ fontSize: 12, marginBottom: 8 }}
                        ellipsis={{ rows: 2 }}>{res.description}</Paragraph>
                    )}

                    {/* Meta */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {res.createdAt ? new Date(res.createdAt).toLocaleDateString('zh-CN') : ''}
                      </Text>
                      <Space size={4}>
                        <Button size="small" type="text" icon={isFav ? <StarFilled style={{ color: '#F59E0B' }} /> : <StarOutlined />}
                          onClick={(e) => { e.stopPropagation(); toggleFavorite(res.id) }} />
                        <Dropdown menu={{ items: [
                          { key: 'view', label: res.type === 'interactive_classroom' ? '进入课堂' : '查看详情', onClick: () => openResource(res) },
                          { key: 'regenerate', label: '重新生成', onClick: () => { setGenContext({ source: 'global', courseId: res.course_id, topic: res.topic }); setGenDrawerOpen(true) } },
                        ]}} trigger={['click']}>
                          <Button size="small" type="text" icon={<MoreOutlined />} onClick={(e) => e.stopPropagation()} />
                        </Dropdown>
                      </Space>
                    </div>
                  </Card>
                </Col>
              )
            })}
          </Row>
        )}
      </div>

      {/* ── Generate Drawer ── */}
      <ResourceGenerateDrawer
        visible={genDrawerOpen}
        onClose={() => setGenDrawerOpen(false)}
        onGenerated={() => { reload(); setGenDrawerOpen(false) }}
        context={genContext}
      />

    </div>
  )
}
