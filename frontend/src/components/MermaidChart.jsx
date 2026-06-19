import { useEffect, useRef, useState, useCallback } from 'react'
import { Spin, Typography, Button } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { useTheme } from '../contexts/ThemeContext'

const { Text } = Typography

// mermaid 11.x 初始化（可在切换主题时重复调用更新 theme）
async function initMermaid(theme) {
  const mermaid = (await import('mermaid')).default
  mermaid.initialize({
    startOnLoad: false,
    theme,
    securityLevel: 'loose',
  })
  return mermaid
}

// 清理 mermaid 语法中的常见 11.x 不兼容问题
function sanitizeChart(text) {
  let s = text.trim()
  // 合并 3+ 连续空行为双空行
  s = s.replace(/\n{3,}/g, '\n\n')
  // <br/> 自闭合 → <br>（mermaid 11.x 严格 HTML）
  s = s.replace(/<br\s*\/>/gi, '<br>')
  return s
}

/**
 * 图表渲染器（封装 mermaid 11.x）
 *
 * @param {Object} props
 * @param {string} props.chart - Mermaid 语法文本
 * @param {boolean} props.loading - 加载中
 * @param {string} props.theme - 主题: 'default' | 'dark' | 'neutral' | 'forest'
 */
export default function MermaidChart({ chart = '', loading = false, theme = 'default' }) {
  const { resolved } = useTheme()
  const effectiveTheme = resolved === 'dark' ? 'dark' : theme

  const containerRef = useRef(null)
  const [errorText, setErrorText] = useState('')
  const renderIdRef = useRef(0)

  const doRender = useCallback(async () => {
    if (!chart || !containerRef.current) return

    const renderId = ++renderIdRef.current
    const svgId = `mermaid-svg-${renderId}`

    try {
      setErrorText('')
      const mermaid = await initMermaid(effectiveTheme)

      const cleanChart = sanitizeChart(chart)

      const { svg } = await mermaid.render(svgId, cleanChart)
      if (renderId === renderIdRef.current && containerRef.current) {
        containerRef.current.innerHTML = svg
      }
    } catch (err) {
      if (renderId === renderIdRef.current) {
        console.error('Mermaid rendering error:', err)
        setErrorText(err.message || '图表渲染失败')
      }
    }
  }, [chart, effectiveTheme])

  useEffect(() => {
    doRender()
  }, [doRender])

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
        <Spin tip="渲染图表..." />
      </div>
    )
  }

  if (errorText) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column',
        justifyContent: 'center', alignItems: 'center', minHeight: 200, gap: 12,
      }}>
        <Text type="danger">⚠️ 图表渲染错误: {errorText}</Text>
        <Button icon={<ReloadOutlined />} onClick={doRender} size="small">重新渲染</Button>
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
