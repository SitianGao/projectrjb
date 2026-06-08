import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Typography } from 'antd'

/**
 * Markdown 渲染器（基于 react-markdown + remark-gfm）
 *
 * 支持：表格、任务列表、代码高亮、数学公式（如需可扩展）
 *
 * @param {Object} props
 * @param {string} props.content - Markdown 文本
 * @param {boolean} props.compact - 紧凑模式（减小间距）
 */
export default function MarkdownRenderer({ content = '', compact = false }) {
  return (
    <div style={compact ? { fontSize: 14, lineHeight: 1.7 } : { fontSize: 15, lineHeight: 1.8 }}>
      <Typography>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '')
              const codeStr = String(children).replace(/\n$/, '')
              return !inline && match ? (
                <SyntaxHighlighter
                  style={oneLight}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {codeStr}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              )
            },
            // 链接在新标签页打开
            a({ href, children, ...props }) {
              return (
                <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                  {children}
                </a>
              )
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </Typography>
    </div>
  )
}
