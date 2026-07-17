import { Alert, Button } from 'antd'

export default function ChatErrorCard({ error, onRetry }) {
  if (!error) return null
  return (
    <Alert
      type="error"
      showIcon
      message={error.message || '请求失败'}
      action={onRetry ? <Button size="small" onClick={onRetry}>重试</Button> : null}
      className="chat-error-card"
    />
  )
}
