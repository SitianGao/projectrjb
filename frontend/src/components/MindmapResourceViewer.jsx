import { useMemo } from 'react'
import { Empty } from 'antd'
import { normalizeLegacyContent } from '../utils/resourceNormalizer'
import MindMapViewer from './MindMapViewer'

/**
 * 将 JSON 树结构 { label, description, children } 递归转为 Markdown 大纲字符串，
 * 供 MindMapViewer (markmap) 渲染为交互式思维导图。
 */
function treeToMarkdown(node, depth = 0) {
  const label = typeof node === 'string' ? node : (node.label || node.title || node.name || '')
  const desc = node.description || ''
  const kids = node.children || []

  // depth 0 是根节点，用 #；子节点用 ## / ### / #### ...
  const prefix = depth === 0 ? '# ' : `${'#'.repeat(depth + 1)} `
  const descLine = desc ? `\n> ${desc}\n` : ''
  let md = `${prefix}${label}${descLine}\n`

  for (const child of kids) {
    md += treeToMarkdown(child, depth + 1)
  }
  return md
}

/**
 * 思维导图资源查看器 — 将 resource.content（JSON 树）转为 Markdown，用 markmap 渲染。
 */
export default function MindmapResourceViewer({ resource }) {
  const content = normalizeLegacyContent(resource) || resource?.content
  const root = content?.root || content
  const children = root?.children || (Array.isArray(content) ? content : [])

  const markdown = useMemo(() => {
    if (!root?.label && !children.length) return ''
    // 如果有 root.label，以 root 为根；否则以 topic 或 "知识点" 为根
    const tree = root?.label
      ? root
      : { label: resource?.topic || '知识点', children }
    return treeToMarkdown(tree)
  }, [root, children, resource?.topic])

  if (!markdown) {
    return <Empty description="思维导图数据加载中..." image={Empty.PRESENTED_IMAGE_SIMPLE} />
  }

  return <MindMapViewer content={markdown} />
}
