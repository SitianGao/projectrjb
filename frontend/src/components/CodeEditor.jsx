import { useRef, useCallback } from 'react'
import { Segmented, Space, Typography } from 'antd'
import { CodeOutlined } from '@ant-design/icons'

const { Text } = Typography

const LANG_OPTIONS = [
  { label: 'Python', value: 'python' },
  { label: 'C', value: 'c' },
  { label: 'C++', value: 'cpp' },
  { label: 'Java', value: 'java' },
]

/**
 * Code Editor with language selector.
 * Uses a simple textarea fallback when Monaco is loading or unavailable.
 */
export default function CodeEditor({
  language = 'python',
  onLanguageChange,
  value = '',
  onChange,
  readOnly = false,
  height = 400,
}) {
  const textareaRef = useRef(null)

  const handleChange = useCallback((e) => {
    onChange?.(e.target.value)
  }, [onChange])

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 8,
      overflow: 'hidden',
      background: 'var(--bg-card)',
    }}>
      {/* Language Selector Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 12px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-page)',
      }}>
        <Space>
          <CodeOutlined />
          <Text strong style={{ fontSize: 13 }}>代码编辑器</Text>
        </Space>
        <Segmented
          size="small"
          options={LANG_OPTIONS}
          value={language}
          onChange={onLanguageChange}
        />
      </div>

      {/* Editor Area — textarea fallback (Monaco loads async) */}
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        readOnly={readOnly}
        spellCheck={false}
        style={{
          width: '100%',
          height,
          minHeight: height,
          padding: '12px 16px',
          border: 'none',
          outline: 'none',
          resize: 'vertical',
          fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
          fontSize: 14,
          lineHeight: 1.6,
          background: '#1e1e2e',
          color: '#cdd6f4',
          tabSize: 4,
        }}
      />
    </div>
  )
}
