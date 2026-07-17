import { useEffect, useRef } from 'react'
import { Empty, Typography } from 'antd'
import { normalizeLegacyContent } from '../utils/resourceNormalizer'

const { Text } = Typography

/**
 * Render mindmap using nested list rendering (compatible with markmap-style).
 */
export default function MindmapResourceViewer({ resource }) {
  const content = normalizeLegacyContent(resource) || resource?.content
  const containerRef = useRef(null)

  const root = content?.root || content
  const children = root?.children || (Array.isArray(content) ? content : [])

  const renderNodes = (nodes, depth = 0) => {
    if (!nodes?.length) return null
    return (
      <ul style={{ paddingLeft: depth === 0 ? 0 : 20, listStyle: 'none', margin: 0 }}>
        {nodes.map((node, i) => {
          const label = typeof node === 'string' ? node : (node.label || node.title || node.name || '')
          const kids = node.children || []
          const desc = node.description || ''
          return (
            <li key={i} style={{ marginBottom: depth === 0 ? 12 : 4 }}>
              <div style={{
                padding: depth === 0 ? '10px 16px' : '6px 12px',
                borderRadius: depth === 0 ? 12 : 8,
                background: depth === 0 ? '#F3F0FF' : depth === 1 ? '#FAFAFC' : 'transparent',
                border: depth === 0 ? '1.5px solid #6C5CE7' : depth === 1 ? '1px solid #E5E7EB' : 'none',
                fontWeight: depth === 0 ? 600 : 400,
                fontSize: depth === 0 ? 15 : depth === 1 ? 13 : 12,
                color: '#111827',
                cursor: 'default',
              }}>
                {label}
                {desc && <div style={{ fontSize: 11, color: '#6B7280', fontWeight: 400, marginTop: 2 }}>{desc}</div>}
              </div>
              {kids.length > 0 && renderNodes(kids, depth + 1)}
            </li>
          )
        })}
      </ul>
    )
  }

  if (!children.length && !root?.label) {
    return <Empty description="思维导图数据加载中..." image={Empty.PRESENTED_IMAGE_SIMPLE} />
  }

  return (
    <div ref={containerRef} style={{ maxWidth: 780, margin: '0 auto', padding: '8px 0' }}>
      {root?.label && (
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <div style={{
            display: 'inline-block', padding: '14px 24px', borderRadius: 16,
            background: 'linear-gradient(135deg, #6C5CE7, #A78BFA)', color: '#fff',
            fontSize: 16, fontWeight: 700,
          }}>
            {root.label}
          </div>
        </div>
      )}
      {renderNodes([
        ...(root?.label ? children : [{ label: resource?.topic || '知识点', children }]),
      ])}
    </div>
  )
}
