import { Button, Space } from 'antd'
import {
  BulbOutlined,
  RobotOutlined,
  PushpinOutlined,
} from '@ant-design/icons'
import { useEffect, useState } from 'react'

/**
 * Floating mini-toolbar that appears when text is selected.
 * Positioned near the selection bounding rect.
 *
 * Props:
 *   rect       — { top, bottom, left, width } from getBoundingClientRect
 *   visible    — boolean
 *   onExplain  — () => void  (opens tutor drawer with selected text)
 *   onAskAI    — () => void  (opens tutor drawer with "我不理解..." prompt)
 *   onAddNote  — () => void  (save to notes)
 */
export default function TextSelectionToolbar({
  rect,
  visible,
  onExplain,
  onAskAI,
  onAddNote,
}) {
  const [style, setStyle] = useState({ display: 'none' })

  useEffect(() => {
    if (!visible || !rect) {
      setStyle({ display: 'none' })
      return
    }

    const toolbarW = 260
    const toolbarH = 40
    const gap = 8

    // Position above selection if there's room, otherwise below
    let top = rect.top - toolbarH - gap
    if (top < 10) {
      top = rect.bottom + gap
    }

    // Center over the selection, clamp to viewport
    let left = rect.left - toolbarW / 2
    if (left < 8) left = 8
    if (left + toolbarW > window.innerWidth - 8) {
      left = window.innerWidth - toolbarW - 8
    }

    setStyle({
      position: 'fixed',
      top,
      left,
      zIndex: 1100,
      display: 'flex',
    })
  }, [visible, rect])

  return (
    <div
      className="text-selection-toolbar"
      style={style}
      onMouseDown={(e) => e.preventDefault()} // prevent selection loss
    >
      <Space size={4}>
        <Button
          size="small"
          icon={<BulbOutlined />}
          onClick={onExplain}
        >
          解释一下
        </Button>
        <Button
          size="small"
          type="primary"
          icon={<RobotOutlined />}
          onClick={onAskAI}
        >
          问 AI
        </Button>
        <Button
          size="small"
          icon={<PushpinOutlined />}
          onClick={onAddNote}
        >
          加入笔记
        </Button>
      </Space>
    </div>
  )
}
