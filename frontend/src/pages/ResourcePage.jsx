import { useState, useEffect } from 'react'
import { Row, Col, Typography, Input, Select, Space, Button, Empty, Pagination } from 'antd'
import { SearchOutlined, FilterOutlined, ReloadOutlined } from '@ant-design/icons'
import ResourceCard from '../components/ResourceCard'
import MindMapViewer from '../components/MindMapViewer'
import MermaidChart from '../components/MermaidChart'
import MarkdownRenderer from '../components/MarkdownRenderer'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { getResources } from '../api/resource'

const { Title } = Typography

const TYPE_OPTIONS = [
  { value: '', label: '全部类型' },
  { value: 'document', label: '文档' },
  { value: 'quiz', label: '练习题' },
  { value: 'mindmap', label: '思维导图' },
]

/**
 * 学习资源页 — 资源卡片列表 + 筛选 + 详情预览
 */
export default function ResourcePage() {
  const [resources, setResources] = useState([])
  const [loading, setLoading] = useState(true)
  const [keyword, setKeyword] = useState('')
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [preview, setPreview] = useState(null) // 当前预览的资源

  const pageSize = 12

  useEffect(() => {
    loadResources()
  }, [page, type])

  async function loadResources() {
    setLoading(true)
    try {
      const params = { page, page_size: pageSize, keyword, type: type || undefined }
      const data = await getResources(params)
      setResources(Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [])
      setTotal(data?.total || 0)
    } catch {
      // 模拟数据
      const mockResources = [
        { id: '1', type: 'document', title: '二次函数知识点总结', description: '系统梳理二次函数的核心概念、图像特征与常见题型解题技巧', tags: ['数学', '函数', '初中'], createdAt: new Date() },
        { id: '2', type: 'quiz', title: '力学基础练习题', description: '涵盖牛顿三大定律、受力分析等基础概念的练习题目', tags: ['物理', '力学'], createdAt: new Date(Date.now() - 3600000) },
        { id: '3', type: 'mindmap', title: '英语语法体系', description: '以思维导图形式展示英语时态、语态、从句等语法框架', tags: ['英语', '语法'], createdAt: new Date(Date.now() - 7200000) },
        { id: '4', type: 'document', title: '电路分析方法', description: '讲解串并联电路、基尔霍夫定律等电路分析核心方法', tags: ['物理', '电学'], createdAt: new Date(Date.now() - 86400000) },
        { id: '5', type: 'quiz', title: '二次函数专项练习', description: '精选二次函数典型例题，涵盖图像判断、最值问题等题型', tags: ['数学', '函数'], createdAt: new Date(Date.now() - 172800000) },
        { id: '6', type: 'mindmap', title: '初中数学知识体系', description: '覆盖初中数学全部章节的知识结构思维导图', tags: ['数学', '综合'], createdAt: new Date(Date.now() - 259200000) },
      ]
      setResources(mockResources)
      setTotal(6)
    } finally {
      setLoading(false)
    }
  }

  function handleSearch() {
    setPage(1)
    loadResources()
  }

  function handlePreview(resource) {
    setPreview(resource)
  }

  function handleDownload(resource) {
    console.log('Download:', resource.id)
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0 }}>学习资源</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadResources}>刷新</Button>
        </Space>
      </div>

      {/* 搜索 + 筛选 */}
      <div style={{ marginTop: 16, marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="搜索资源..."
            prefix={<SearchOutlined />}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 240 }}
            allowClear
          />
          <Select
            value={type}
            onChange={setType}
            options={TYPE_OPTIONS}
            style={{ width: 140 }}
          />
          <Button type="primary" icon={<FilterOutlined />} onClick={handleSearch}>
            筛选
          </Button>
        </Space>
      </div>

      {/* 资源卡片网格 */}
      {loading ? (
        <LoadingSkeleton type="card" count={6} />
      ) : resources.length === 0 ? (
        <Empty description="没有找到符合条件的资源" />
      ) : (
        <>
          <Row gutter={[16, 16]}>
            {resources.map((r) => (
              <Col xs={24} sm={12} md={8} lg={6} key={r.id}>
                <ResourceCard
                  resource={r}
                  onClick={handlePreview}
                  onDownload={handleDownload}
                />
              </Col>
            ))}
          </Row>
          {total > pageSize && (
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <Pagination
                current={page}
                pageSize={pageSize}
                total={total}
                onChange={setPage}
                showSizeChanger={false}
              />
            </div>
          )}
        </>
      )}

      {/* 资源详情预览抽屉（内联） */}
      {preview && (
        <div style={{ marginTop: 32, borderTop: '1px solid #f0f0f0', paddingTop: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <Title level={4} style={{ margin: 0 }}>
              预览：{preview.title}
            </Title>
            <Button onClick={() => setPreview(null)}>关闭预览</Button>
          </div>

          {preview.type === 'mindmap' ? (
            <MindMapViewer
              content={`# ${preview.title}\n## 概述\n${preview.description}\n## 核心概念\n- 概念A\n- 概念B\n## 应用\n- 应用1\n- 应用2`}
            />
          ) : preview.type === 'document' ? (
            <MarkdownRenderer
              content={`# ${preview.title}\n\n${preview.description}\n\n## 正文内容\n\n这里将显示文档的完整 Markdown 内容...`}
            />
          ) : preview.type === 'quiz' ? (
            <MermaidChart
              chart={`graph TD\n  A[${preview.title}] --> B[基础题]\n  A --> C[进阶题]\n  A --> D[综合题]\n  B --> E[选择题]\n  B --> F[填空题]`}
            />
          ) : null}
        </div>
      )}
    </div>
  )
}
