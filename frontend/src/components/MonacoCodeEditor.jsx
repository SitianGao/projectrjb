import { useRef, useCallback, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import { Space, Typography, Button, Tooltip, message } from 'antd'
import { CodeOutlined, UndoOutlined, CopyOutlined } from '@ant-design/icons'

const { Text } = Typography

/**
 * Monaco Code Editor — Python 实验代码编辑器。
 * 封装 @monaco-editor/react，提供实验场景所需的只读切换、重置、复制等功能。
 */
export default function MonacoCodeEditor({
  value = '',
  onChange,
  readOnly = false,
  height = 400,
  language = 'python',
  onEditorMount,
  showToolbar = true,
  title = '代码编辑器',
}) {
  const editorRef = useRef(null)

  const handleMount = useCallback((editor, monaco) => {
    editorRef.current = editor
    // Python 基本配置
    monaco.editor.setTheme('vs-dark')
    onEditorMount?.(editor, monaco)
  }, [onEditorMount])

  const handleChange = useCallback((val) => {
    onChange?.(val || '')
  }, [onChange])

  const handleCopy = useCallback(() => {
    if (value) {
      navigator.clipboard.writeText(value).then(() => {
        message.success('代码已复制到剪贴板')
      }).catch(() => {
        message.warning('复制失败，请手动复制')
      })
    }
  }, [value])

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 8,
      overflow: 'hidden',
      background: '#1e1e2e',
    }}>
      {/* Toolbar */}
      {showToolbar && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '6px 12px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--bg-page, #2b2b3d)',
        }}>
          <Space size={8}>
            <CodeOutlined style={{ color: '#89b4fa' }} />
            <Text strong style={{ fontSize: 13, color: '#cdd6f4' }}>{title}</Text>
          </Space>
          <Space size={4}>
            <Tooltip title="复制代码">
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={handleCopy}
                style={{ color: '#a6adc8' }}
              />
            </Tooltip>
          </Space>
        </div>
      )}

      {/* Monaco Editor */}
      <Editor
        height={height}
        language={language}
        value={value}
        onChange={handleChange}
        onMount={handleMount}
        options={{
          readOnly,
          fontSize: 14,
          fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
          lineHeight: 1.6,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          tabSize: 4,
          insertSpaces: true,
          renderLineHighlight: 'line',
          bracketPairColorization: { enabled: true },
          padding: { top: 12, bottom: 12 },
        }}
        theme="vs-dark"
      />
    </div>
  )
}
