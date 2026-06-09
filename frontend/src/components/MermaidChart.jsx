import { useEffect, useRef, useState } from 'react'
import { Spin, Typography, message } from 'antd'

const { Text } = Typography

/**
 * 图表渲染器（封装 mermaid）
 *
 * @param {Object} props
 * @param {string} props.chart - Mermaid 语法文本
 * @param {boolean} props.loading - 加载中
 * @param {string} props.theme - 主题: 'default' | 'dark' | 'neutral' | 'forest'
 */
export default function MermaidChart({ chart = '', loading = false, theme = 'default' }) {
  const containerRef = useRef(null)
  const [errorText, setErrorText] = useState('')
  const idRef = useRef(`mermaid-${Math.random().toString(36).slice(2, 8)}`)

  useEffect(() => {
    if (!chart || !containerRef.current) return

    let cancelled = false

    ;(async () => {
      try {
        setErrorText('')
        const mermaid = (await import('mermaid')).default

        mermaid.initialize({
          startOnLoad: false,
          theme,
          securityLevel: 'loose',
        })

        const { svg } = await mermaid.render(idRef.current, chart)
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg
        }
      } catch (err) {
        if (!cancelled) {
          console.error('Mermaid rendering error:', err)
          setErrorText(err.message || '图表渲染失败')
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [chart, theme])

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
        <Spin tip="渲染图表..." />
      </div>
    )
  }

  if (errorText) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
        <Text type="danger">图表渲染错误: {errorText}</Text>
      </div>
    )
  }

  if (!chart) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
        <Text type="secondary">暂无图表内容</Text>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', overflowX: 'auto', display: 'flex', justifyContent: 'center' }}
    />
  )
}
