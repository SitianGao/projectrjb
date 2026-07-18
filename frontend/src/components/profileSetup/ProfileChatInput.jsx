import { useState } from 'react'
import { Button, Input } from 'antd'
import { SendOutlined } from '@ant-design/icons'

export default function ProfileChatInput({ onSend, loading }) {
  const [value, setValue] = useState('')
  const submit = () => {
    const text = value.trim()
    if (!text || loading) return
    onSend(text)
    setValue('')
  }
  return (
    <div className="profile-chat-input">
      <Input.TextArea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onPressEnter={(event) => {
          if (!event.shiftKey) {
            event.preventDefault()
            submit()
          }
        }}
        autoSize={{ minRows: 2, maxRows: 4 }}
        disabled={loading}
        placeholder="描述你的目标、基础、薄弱点、学习时间或资源偏好..."
      />
      <Button type="primary" icon={<SendOutlined />} loading={loading} disabled={!value.trim()} onClick={submit}>
        发送
      </Button>
    </div>
  )
}
