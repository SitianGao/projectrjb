import { useState, useEffect } from 'react'
import { Drawer, Button, Input, message, Space, Typography } from 'antd'
import { SaveOutlined, ExportOutlined, PushpinOutlined } from '@ant-design/icons'

const { TextArea } = Input
const { Text } = Typography

const STORAGE_KEY = 'classroom_notes'

function loadNotes() {
  try {
    return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

function saveNotes(notes) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(notes))
}

export default function ClassroomNotesDrawer({ open, onClose, sceneId, sceneTitle }) {
  const [notes, setNotes] = useState({})

  useEffect(() => {
    if (open) setNotes(loadNotes())
  }, [open])

  const currentNote = notes[sceneId] || ''
  const hasSaved = !!currentNote.trim()

  const handleSave = () => {
    const all = { ...notes, [sceneId]: currentNote }
    saveNotes(all)
    message.success('笔记已保存')
  }

  const handleChange = (e) => {
    const value = e.target.value
    setNotes((prev) => {
      const next = { ...prev, [sceneId]: value }
      // Auto-save on change
      saveNotes(next)
      return next
    })
  }

  const handleExport = () => {
    const all = loadNotes()
    const text = Object.entries(all)
      .filter(([, v]) => v.trim())
      .map(([k, v]) => `## ${k}\n\n${v}`)
      .join('\n\n---\n\n')
    const blob = new Blob([text], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '课堂笔记.md'
    a.click()
    URL.revokeObjectURL(url)
    message.success('笔记已导出')
  }

  return (
    <Drawer
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <EditOutlined style={{ color: '#6C5CE7' }} />
          <span>课堂笔记</span>
          {sceneTitle && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              — {sceneTitle}
            </Text>
          )}
        </div>
      }
      placement="right"
      open={open}
      onClose={onClose}
      width={380}
      styles={{
        body: { padding: '20px 24px', display: 'flex', flexDirection: 'column', height: '100%' },
        header: { borderBottom: '1px solid rgba(0,0,0,0.06)' },
      }}
      mask={false}
      style={{ position: 'absolute' }}
    >
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <TextArea
          value={currentNote}
          onChange={handleChange}
          placeholder="在此记录本页重点…（自动保存）"
          style={{
            flex: 1,
            minHeight: 300,
            borderRadius: 10,
            border: '1px solid rgba(0,0,0,0.08)',
            fontSize: 14,
            lineHeight: 1.7,
            resize: 'none',
          }}
        />

        <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
          <Button
            icon={<SaveOutlined />}
            onClick={handleSave}
            type={hasSaved ? 'default' : 'primary'}
            style={{ borderRadius: 8, flex: 1 }}
          >
            保存
          </Button>
          <Button
            icon={<ExportOutlined />}
            onClick={handleExport}
            style={{ borderRadius: 8 }}
          >
            导出
          </Button>
        </div>

        <Text type="secondary" style={{ fontSize: 11, marginTop: 12, textAlign: 'center' }}>
          笔记自动保存到浏览器，导出为 Markdown 文件
        </Text>
      </div>
    </Drawer>
  )
}
