import { useEffect, useRef } from 'react'
import { Spin, Typography } from 'antd'
import { Transformer } from 'markmap-lib'
import { Markmap } from 'markmap-view'

const { Text } = Typography

/**
 * 思维导图查看器（封装 markmap）
 *
 * 将 Markdown 格式文本渲染为交互式思维导图。
 *
 * @param {Object} props
 * @param {string} props.content - Markdown 格式的思维导图内容
 * @param {Object} props.options - markmap 配置选项
 * @param {boolean} props.loading - 加载中
 */
export default function MindMapViewer({ content = '', options = {}, loading = false }) {
  const containerRef = useRef(null)
  const markmapRef = useRef(null)

  useEffect(() => {
    if (!content || !containerRef.current) return

    ;(async () => {
      try {
        const transformer = new Transformer()
        const { root } = transformer.transform(content)

        if (markmapRef.current) {
          markmapRef.current.setData(root)
        } else {
          markmapRef.current = Markmap.create(
            containerRef.current,
            {
              autoFit: true,
              duration: 500,
              ...options,
            },
            root,
          )
        }
      } catch (err) {
        console.error('MindMap rendering error:', err)
      }
    })()

    return () => {
      // markmap 实例不主动销毁，便于复用
    }
  }, [content, options])

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <Spin tip="加载思维导图..." />
      </div>
    )
  }

  if (!content) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
        <Text type="secondary">暂无思维导图内容</Text>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', minHeight: 400, height: '60vh' }}
    />
  )
}
