import { useEffect, useRef, useState } from 'react'
import { Spin, Typography, Button } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
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
  const svgRef = useRef(null)
  const markmapRef = useRef(null)
  const [error, setError] = useState(null)
  const [retryKey, setRetryKey] = useState(0)

  useEffect(() => {
    if (!content || !svgRef.current) return

    setError(null)

    ;(async () => {
      try {
        const transformer = new Transformer()
        const { root } = transformer.transform(content)

        if (markmapRef.current) {
          markmapRef.current.setData(root)
        } else {
          // Markmap.create 需要 SVG 元素，不是 div
          markmapRef.current = Markmap.create(
            svgRef.current,
            {
              autoFit: true,
              duration: 500,
              ...options,
            },
            root,
          )
        }
      } catch (err) {
        console.error('[MindMapViewer] rendering error:', err)
        setError(err.message || '思维导图渲染失败')
      }
    })()

    return () => {
      // markmap 实例不主动销毁，便于复用
    }
  }, [content, options, retryKey])

  const handleRetry = () => setRetryKey((k) => k + 1)

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <Spin tip="加载思维导图..." />
      </div>
    )
  }

  if (error) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column',
        justifyContent: 'center', alignItems: 'center', minHeight: 200, gap: 12,
      }}>
        <Text type="danger">⚠️ {error}</Text>
        <Button icon={<ReloadOutlined />} onClick={handleRetry} size="small">重新渲染</Button>
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
    <div style={{ width: '100%', minHeight: 400, height: '60vh', position: 'relative' }}>
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        style={{ position: 'absolute', top: 0, left: 0 }}
      />
    </div>
  )
}
