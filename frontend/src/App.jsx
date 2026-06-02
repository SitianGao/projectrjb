import { useState } from 'react'
import { Input, Button, Card, Typography, Divider, Spin } from 'antd'

const { TextArea } = Input
const { Title } = Typography

function App() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [profile, setProfile] = useState(null)

  const sendMessage = async () => {
    if (!message) return

    setLoading(true)
    setProfile(null)

    try {
      const res = await fetch('http://127.0.0.1:8001/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
      })

      const data = await res.json()
      setProfile(data.reply)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 700, margin: '50px auto', fontFamily: 'Arial' }}>
      
      <Title level={2}>🎓 EduAgent 学习智能体 MVP</Title>

      <TextArea
        rows={4}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="请输入学生信息，例如：我是计算机大二学生，想考研，数学较弱"
      />

      <Button
        type="primary"
        onClick={sendMessage}
        loading={loading}
        style={{ marginTop: 10 }}
      >
        生成学生画像
      </Button>

      <Divider />

      {loading && <Spin tip="AI正在分析学生画像..." />}

      {profile && (
        <Card title="🧠 学生6维画像" bordered={true}>
          <p><b>知识水平：</b> {profile.knowledge_level}</p>
          <p><b>学习目标：</b> {profile.learning_goal}</p>
          <p><b>薄弱知识点：</b> {profile.weak_points?.join(', ')}</p>
          <p><b>兴趣方向：</b> {profile.interest?.join(', ')}</p>
          <p><b>学习风格：</b> {profile.study_style}</p>
          <p><b>资源偏好：</b> {profile.preferred_resources?.join(', ')}</p>
          <p><b>分析结果：</b> {profile.analysis}</p>
        </Card>
      )}

    </div>
  )
}

export default App