import { Tag, List, Typography, Empty, Collapse, Spin } from 'antd'
import {
  BookOutlined,
  NodeIndexOutlined,
  LinkOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import MermaidChart from './MermaidChart'

const { Text, Title } = Typography

const STYLE_LABELS = {
  analogy: { label: '类比法', color: 'orange', icon: '🔗' },
  formula: { label: '公式法', color: 'blue', icon: '📐' },
  visual: { label: '图解法', color: 'purple', icon: '📊' },
  story: { label: '故事法', color: 'green', icon: '📖' },
}

/**
 * 右侧知识面板 — 展示 Mermaid 图表、参考知识点、解释风格
 *
 * @param {Object} props
 * @param {Array<{title: string, chart: string}>} props.diagrams - Mermaid 图表列表
 * @param {Array<{title: string, description?: string}>} props.references - 参考知识点
 * @param {string} props.explanationStyle - 当前解释风格
 * @param {boolean} props.loading - 是否正在生成
 */
export default function KnowledgePanel({
  diagrams = [],
  references = [],
  explanationStyle = '',
  loading = false,
}) {
  const styleInfo = STYLE_LABELS[explanationStyle] || null

  const isEmpty = diagrams.length === 0 && references.length === 0

  return (
    <div style={{
      width: '100%', height: '100%',
      display: 'flex', flexDirection: 'column',
      background: 'var(--bg-card, #fff)',
      borderLeft: '1px solid var(--border, #f0f0f0)',
      overflow: 'hidden',
    }}>
      {/* 标题栏 */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid var(--border, #f0f0f0)',
        flexShrink: 0,
      }}>
        <Title level={5} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <BulbOutlined style={{ color: '#8b5cf6' }} />
          知识参考
        </Title>
        {styleInfo && (
          <Tag color={styleInfo.color} style={{ marginTop: 8 }}>
            {styleInfo.icon} {styleInfo.label}
          </Tag>
        )}
      </div>

      {/* 内容区 */}
      <div style={{ flex: 1, overflowY: 'auto', minHeight: 0, padding: '12px 16px' }}>
        {isEmpty && !loading ? (
          <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            justifyContent: 'center', height: '100%', minHeight: 200,
          }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Text type="secondary" style={{ fontSize: 13 }}>
                  开始对话后，相关的知识点<br />和图表会显示在这里
                </Text>
              }
            />
          </div>
        ) : (
          <>
            {/* Mermaid 图表区 */}
            {diagrams.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Text strong style={{ fontSize: 14, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                  <NodeIndexOutlined style={{ color: '#8b5cf6' }} />
                  图表展示
                </Text>
                {diagrams.map((d, i) => (
                  <div key={i} style={{
                    marginBottom: 12,
                    borderRadius: 10,
                    border: '1px solid var(--border)',
                    padding: 10,
                    background: 'var(--surface-secondary)',
                  }}>
                    {d.title && (
                      <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
                        {d.title}
                      </Text>
                    )}
                    <MermaidChart chart={d.chart} theme="default" />
                  </div>
                ))}
              </div>
            )}

            {/* 参考知识点 */}
            {references.length > 0 && (
              <div>
                <Text strong style={{ fontSize: 14, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                  <BookOutlined style={{ color: '#1677ff' }} />
                  参考资料
                </Text>
                <List
                  size="small"
                  dataSource={references}
                  renderItem={(ref, i) => (
                    <List.Item key={i} style={{
                      padding: '8px 12px',
                      borderRadius: 8,
                      marginBottom: 6,
                      background: 'var(--surface-secondary)',
                      border: 'none',
                    }}>
                      <List.Item.Meta
                        avatar={<LinkOutlined style={{ color: '#1677ff', fontSize: 12 }} />}
                        title={<Text style={{ fontSize: 13 }}>{ref.title}</Text>}
                        description={ref.description ? <Text type="secondary" style={{ fontSize: 12 }}>{ref.description}</Text> : null}
                      />
                    </List.Item>
                  )}
                />
              </div>
            )}

            {/* 生成中提示 */}
            {loading && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, marginTop: 24 }}>
                <Spin size="default" />
                <Text type="secondary" style={{ fontSize: 13 }}>正在分析知识点...</Text>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
