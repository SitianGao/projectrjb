import { Card, Collapse, Tag, Typography } from 'antd'
import { AimOutlined, BulbOutlined, WarningOutlined } from '@ant-design/icons'
import MarkdownRenderer from './MarkdownRenderer'
import { normalizeLegacyContent } from '../utils/resourceNormalizer'

const { Text, Title, Paragraph } = Typography

/**
 * Render document resource — structured sections or legacy Markdown.
 */
export default function DocumentResourceViewer({ resource }) {
  const content = normalizeLegacyContent(resource) || resource?.content

  // Legacy: plain Markdown string
  if (typeof content === 'string') {
    return <MarkdownRenderer content={content} />
  }

  // Structured document
  const sections = content?.sections || []
  const objectives = content?.learning_objectives || []
  const mistakes = content?.common_mistakes || []
  const summary = content?.summary || ''

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      {/* Learning objectives */}
      {objectives.length > 0 && (
        <Card size="small" style={{ marginBottom: 20, borderRadius: 12, background: '#F3F0FF', border: '1px solid #E5E7EB' }}>
          <Text strong style={{ color: '#6C5CE7', display: 'block', marginBottom: 8 }}><AimOutlined /> 学习目标</Text>
          <ul style={{ margin: 0, paddingLeft: 20, color: '#374151', fontSize: 13, lineHeight: 1.8 }}>
            {objectives.map((o, i) => <li key={i}>{o}</li>)}
          </ul>
        </Card>
      )}

      {/* Sections */}
      {sections.length > 0 ? sections.map((section, si) => (
        <div key={si} style={{ marginBottom: 24 }}>
          {section.heading && (
            <Title level={3} style={{ color: '#111827', fontSize: 18, marginBottom: 12 }}>{section.heading}</Title>
          )}
          {section.paragraphs?.map((p, pi) => (
            <Paragraph key={pi} style={{ fontSize: 14, lineHeight: 1.8, color: '#374151' }}>
              {typeof p === 'string' ? <MarkdownRenderer content={p} compact /> : p}
            </Paragraph>
          ))}
          {section.examples?.length > 0 && (
            <Card size="small" style={{ borderRadius: 10, background: '#FAFAFC', border: '1px solid #E5E7EB', marginTop: 8 }}>
              <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}><BulbOutlined style={{ color: '#F59E0B' }} /> 示例</Text>
              {section.examples.map((ex, ei) => (
                <Paragraph key={ei} style={{ fontSize: 13, color: '#6B7280', margin: '4px 0' }}>{ex}</Paragraph>
              ))}
            </Card>
          )}
          {section.key_points?.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {section.key_points.map((kp, ki) => (
                <Tag key={ki} color="purple" style={{ borderRadius: 6, marginBottom: 4 }}>{kp}</Tag>
              ))}
            </div>
          )}
        </div>
      )) : (
        <Paragraph style={{ color: '#6B7280', textAlign: 'center', padding: 40 }}>
          该文档暂无结构化内容，正在使用原始格式展示。
        </Paragraph>
      )}

      {/* Common mistakes */}
      {mistakes.length > 0 && (
        <Card size="small" style={{ marginTop: 20, borderRadius: 12, background: '#FFF7ED', border: '1px solid #FED7AA' }}>
          <Text strong style={{ color: '#F59E0B', display: 'block', marginBottom: 8 }}><WarningOutlined /> 常见误区</Text>
          <ul style={{ margin: 0, paddingLeft: 20, color: '#374151', fontSize: 13, lineHeight: 1.8 }}>
            {mistakes.map((m, i) => <li key={i}>{m}</li>)}
          </ul>
        </Card>
      )}

      {/* Summary */}
      {summary && (
        <Card size="small" style={{ marginTop: 20, borderRadius: 12, background: '#F0FDF4', border: '1px solid #BBF7D0' }}>
          <Text strong style={{ color: '#22C55E', display: 'block', marginBottom: 6 }}>总结</Text>
          <Paragraph style={{ fontSize: 13, color: '#374151', margin: 0 }}>{summary}</Paragraph>
        </Card>
      )}
    </div>
  )
}
