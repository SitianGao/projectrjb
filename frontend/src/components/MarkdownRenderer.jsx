import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import MermaidChart from './MermaidChart'

const base = {
  fontSize: 15,
  lineHeight: 1.85,
  color: '#1e293b',
}

const heading = (level) => ({
  marginTop: level === 1 ? 0 : 28,
  marginBottom: 12,
  fontWeight: 700,
  color: '#0f172a',
  fontSize: [0, 26, 22, 18, 16, 14, 13][level],
  borderBottom: level <= 2 ? '1px solid #e2e8f0' : 'none',
  paddingBottom: level <= 2 ? 8 : 0,
})

const pStyle = { marginBottom: 14 }

const tableStyle = {
  margin: '16px 0',
  borderCollapse: 'collapse',
  width: '100%',
}

const thStyle = {
  background: '#f1f5f9',
  fontWeight: 600,
  padding: '10px 14px',
  borderBottom: '2px solid #cbd5e1',
  textAlign: 'left',
  fontSize: 14,
  whiteSpace: 'nowrap',
}

const tdStyle = {
  padding: '8px 14px',
  borderBottom: '1px solid #e2e8f0',
  fontSize: 14,
}

const blockquoteStyle = {
  margin: '16px 0',
  padding: '12px 18px',
  borderLeft: '4px solid #8b5cf6',
  background: '#f8f7ff',
  borderRadius: '0 8px 8px 0',
  color: '#475569',
}

const inlineCodeStyle = {
  background: '#f1f5f9',
  padding: '2px 6px',
  borderRadius: 4,
  fontSize: '0.9em',
  fontFamily: "'Fira Code', 'Consolas', monospace",
  color: '#7c3aed',
}

const preStyle = {
  margin: '16px 0',
  borderRadius: 10,
  overflow: 'hidden',
  border: '1px solid #e2e8f0',
}

const hrStyle = {
  border: 'none',
  borderTop: '1px solid #e2e8f0',
  margin: '24px 0',
}

const ulStyle = { marginBottom: 14, paddingLeft: 20 }
const olStyle = { marginBottom: 14, paddingLeft: 20 }
const liStyle = { marginBottom: 4 }

/**
 * Markdown 渲染器（基于 react-markdown + remark-gfm）
 */
export default function MarkdownRenderer({ content = '', compact = false }) {
  const s = compact
    ? { ...base, fontSize: 14, lineHeight: 1.65 }
    : base

  return (
    <div style={{ fontSize: s.fontSize, lineHeight: s.lineHeight, color: s.color }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children, ...props }) => <h1 style={heading(1)} {...props}>{children}</h1>,
          h2: ({ children, ...props }) => <h2 style={heading(2)} {...props}>{children}</h2>,
          h3: ({ children, ...props }) => <h3 style={heading(3)} {...props}>{children}</h3>,
          h4: ({ children, ...props }) => <h4 style={heading(4)} {...props}>{children}</h4>,
          h5: ({ children, ...props }) => <h5 style={heading(5)} {...props}>{children}</h5>,
          h6: ({ children, ...props }) => <h6 style={heading(6)} {...props}>{children}</h6>,

          p: ({ children, ...props }) => <p style={pStyle} {...props}>{children}</p>,

          table: ({ children, ...props }) => (
            <div style={{ overflowX: 'auto' }}>
              <table style={tableStyle} {...props}>{children}</table>
            </div>
          ),
          thead: ({ children, ...props }) => <thead {...props}>{children}</thead>,
          tbody: ({ children, ...props }) => <tbody {...props}>{children}</tbody>,
          tr: ({ children, ...props }) => <tr {...props}>{children}</tr>,
          th: ({ children, ...props }) => <th style={thStyle} {...props}>{children}</th>,
          td: ({ children, ...props }) => <td style={tdStyle} {...props}>{children}</td>,

          blockquote: ({ children, ...props }) => <blockquote style={blockquoteStyle} {...props}>{children}</blockquote>,

          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const codeStr = String(children).replace(/\n$/, '')
            // Mermaid 图表渲染
            if (!inline && match && match[1] === 'mermaid') {
              return (
                <div style={{ margin: '16px 0', borderRadius: 10, border: '1px solid #e2e8f0', padding: 12, background: '#fafafa' }}>
                  <MermaidChart chart={codeStr} theme="default" />
                  <details style={{ marginTop: 8 }}>
                    <summary style={{ fontSize: 12, color: '#94a3b8', cursor: 'pointer' }}>查看原始代码</summary>
                    <pre style={{ fontSize: 12, marginTop: 8, whiteSpace: 'pre-wrap', color: '#64748b' }}>{codeStr}</pre>
                  </details>
                </div>
              )
            }
            return !inline && match ? (
              <div style={preStyle}>
                <SyntaxHighlighter
                  style={oneLight}
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
              <code style={inlineCodeStyle} className={className} {...props}>
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

          hr: (props) => <hr style={hrStyle} {...props} />,

          ul: ({ children, ...props }) => <ul style={ulStyle} {...props}>{children}</ul>,
          ol: ({ children, ...props }) => <ol style={olStyle} {...props}>{children}</ol>,
          li: ({ children, ...props }) => <li style={liStyle} {...props}>{children}</li>,

          img: ({ src, alt, ...props }) => (
            <img src={src} alt={alt} style={{ maxWidth: '100%', borderRadius: 8, margin: '12px 0' }} {...props} />
          ),

          strong: ({ children, ...props }) => <strong style={{ color: '#0f172a', fontWeight: 700 }} {...props}>{children}</strong>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
