import { useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight, oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import MermaidChart from './MermaidChart'
import { useTheme } from '../contexts/ThemeContext'

/**
 * Markdown 渲染器（基于 react-markdown + remark-gfm）
 * 深色模式通过 CSS 变量 + oneDark 代码高亮自动适配
 */
export default function MarkdownRenderer({ content = '', compact = false }) {
  const { resolved } = useTheme()
  const isDark = resolved === 'dark'

  const styles = useMemo(() => {
    const baseFontSize = compact ? 14 : 15
    const baseLineHeight = compact ? 1.65 : 1.85

    return {
      base: {
        fontSize: baseFontSize,
        lineHeight: baseLineHeight,
        color: 'var(--text-primary, #1e293b)',
      },
      heading: (level) => ({
        marginTop: level === 1 ? 0 : 28,
        marginBottom: 12,
        fontWeight: 700,
        color: 'var(--text-primary, #0f172a)',
        fontSize: [0, 26, 22, 18, 16, 14, 13][level],
        borderBottom: level <= 2 ? '1px solid var(--md-border, #e2e8f0)' : 'none',
        paddingBottom: level <= 2 ? 8 : 0,
      }),
      p: { marginBottom: 14 },
      table: { margin: '16px 0', borderCollapse: 'collapse', width: '100%' },
      th: {
        background: 'var(--md-th-bg, #f1f5f9)',
        fontWeight: 600,
        padding: '10px 14px',
        borderBottom: '2px solid var(--md-border, #cbd5e1)',
        textAlign: 'left',
        fontSize: 14,
        whiteSpace: 'nowrap',
      },
      td: {
        padding: '8px 14px',
        borderBottom: '1px solid var(--md-border, #e2e8f0)',
        fontSize: 14,
      },
      blockquote: {
        margin: '16px 0',
        padding: '12px 18px',
        borderLeft: '4px solid #8b5cf6',
        background: 'var(--md-blockquote-bg, #f8f7ff)',
        borderRadius: '0 8px 8px 0',
        color: 'var(--md-blockquote-text, #475569)',
      },
      inlineCode: {
        background: 'var(--md-code-bg, #f1f5f9)',
        padding: '2px 6px',
        borderRadius: 4,
        fontSize: '0.9em',
        fontFamily: "'Fira Code', 'Consolas', monospace",
        color: 'var(--md-code-text, #7c3aed)',
      },
      pre: {
        margin: '16px 0',
        borderRadius: 10,
        overflow: 'hidden',
        border: '1px solid var(--md-border, #e2e8f0)',
      },
      hr: {
        border: 'none',
        borderTop: '1px solid var(--md-border, #e2e8f0)',
        margin: '24px 0',
      },
      mermaidContainer: {
        margin: '16px 0',
        borderRadius: 10,
        border: '1px solid var(--md-border, #e2e8f0)',
        padding: 12,
        background: 'var(--bg-card, #fafafa)',
      },
      ul: { marginBottom: 14, paddingLeft: 20 },
      ol: { marginBottom: 14, paddingLeft: 20 },
      li: { marginBottom: 4 },
    }
  }, [compact])

  const codeStyle = isDark ? oneDark : oneLight

  return (
    <div style={styles.base}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children, ...props }) => <h1 style={styles.heading(1)} {...props}>{children}</h1>,
          h2: ({ children, ...props }) => <h2 style={styles.heading(2)} {...props}>{children}</h2>,
          h3: ({ children, ...props }) => <h3 style={styles.heading(3)} {...props}>{children}</h3>,
          h4: ({ children, ...props }) => <h4 style={styles.heading(4)} {...props}>{children}</h4>,
          h5: ({ children, ...props }) => <h5 style={styles.heading(5)} {...props}>{children}</h5>,
          h6: ({ children, ...props }) => <h6 style={styles.heading(6)} {...props}>{children}</h6>,

          p: ({ children, ...props }) => <p style={styles.p} {...props}>{children}</p>,

          table: ({ children, ...props }) => (
            <div style={{ overflowX: 'auto' }}>
              <table style={styles.table} {...props}>{children}</table>
            </div>
          ),
          thead: ({ children, ...props }) => <thead {...props}>{children}</thead>,
          tbody: ({ children, ...props }) => <tbody {...props}>{children}</tbody>,
          tr: ({ children, ...props }) => <tr {...props}>{children}</tr>,
          th: ({ children, ...props }) => <th style={styles.th} {...props}>{children}</th>,
          td: ({ children, ...props }) => <td style={styles.td} {...props}>{children}</td>,

          blockquote: ({ children, ...props }) => <blockquote style={styles.blockquote} {...props}>{children}</blockquote>,

          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const codeStr = String(children).replace(/\n$/, '')
            if (!inline && match && match[1] === 'mermaid') {
              return (
                <div style={styles.mermaidContainer}>
                  <MermaidChart chart={codeStr} theme="default" />
                  <details style={{ marginTop: 8 }}>
                    <summary style={{ fontSize: 12, color: 'var(--text-muted, #94a3b8)', cursor: 'pointer' }}>查看原始代码</summary>
                    <pre style={{ fontSize: 12, marginTop: 8, whiteSpace: 'pre-wrap', color: 'var(--text-secondary, #64748b)' }}>{codeStr}</pre>
                  </details>
                </div>
              )
            }
            return !inline && match ? (
              <div style={styles.pre}>
                <SyntaxHighlighter
                  style={codeStyle}
                  language={match[1]}
                  PreTag="div"
                  customStyle={{
                    margin: 0,
                    borderRadius: 0,
                    fontSize: 14,
                    padding: '18px 20px',
                  }}
                  {...props}
                >
                  {codeStr}
                </SyntaxHighlighter>
              </div>
            ) : (
              <code style={styles.inlineCode} className={className} {...props}>
                {children}
              </code>
            )
          },

          a: ({ href, children, ...props }) => (
            <a href={href} target="_blank" rel="noopener noreferrer"
              style={{ color: '#8b5cf6', textDecoration: 'underline' }}
              {...props}>
              {children}
            </a>
          ),

          hr: (props) => <hr style={styles.hr} {...props} />,

          ul: ({ children, ...props }) => <ul style={styles.ul} {...props}>{children}</ul>,
          ol: ({ children, ...props }) => <ol style={styles.ol} {...props}>{children}</ol>,
          li: ({ children, ...props }) => <li style={styles.li} {...props}>{children}</li>,

          img: ({ src, alt, ...props }) => (
            <img src={src} alt={alt} style={{ maxWidth: '100%', borderRadius: 8, margin: '12px 0' }} {...props} />
          ),

          strong: ({ children, ...props }) => <strong style={{ color: 'var(--text-primary, #0f172a)', fontWeight: 700 }} {...props}>{children}</strong>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
