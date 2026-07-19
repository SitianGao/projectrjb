import { useState } from 'react'
import { Button, Card, Space, Typography, Select, Switch, message } from 'antd'
import { FilePptOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { generatePpt, getTaskStatus } from '../../api/resource'

const { Text } = Typography

export default function PptGenerationCard({ courseId, taskId, topic, difficulty = '中级', onGenerated }) {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [phase, setPhase] = useState('')
  const [pollTimer, setPollTimer] = useState(null)

  async function handleGenerate() {
    if (!topic) {
      message.warning('请先选择知识点主题')
      return
    }

    setLoading(true)
    setProgress(0)
    setPhase('started')

    try {
      // 调用 PPT 生成 API
      const result = await generatePpt({
        topic,
        difficulty,
        course_id: courseId,
        task_id: taskId,
        search: false,
        ai_image: true,
      })

      const taskId_ = result?.data?.task_id
      if (!taskId_) {
        throw new Error('未获取到任务 ID')
      }

      message.info('PPT 生成任务已创建，正在等待生成完成...')

      // 轮询任务状态
      const timer = setInterval(async () => {
        try {
          const status = await getTaskStatus(taskId_)
          const taskData = status?.data || {}

          setProgress(taskData.progress || 0)
          setPhase(taskData.phase || '')

          if (taskData.status === 'done') {
            clearInterval(timer)
            setPollTimer(null)
            setLoading(false)
            setProgress(100)
            message.success('PPT 生成完成！')
            onGenerated?.(taskData.result)
          } else if (taskData.status === 'failed') {
            clearInterval(timer)
            setPollTimer(null)
            setLoading(false)
            message.error(taskData.message || 'PPT 生成失败')
          }
        } catch (err) {
          console.error('轮询任务状态失败:', err)
        }
      }, 3000) // 每 3 秒轮询一次

      setPollTimer(timer)

    } catch (err) {
      setLoading(false)
      message.error(err.message || 'PPT 生成失败')
    }
  }

  return (
    <Card
      className="workspace-tool-card"
      title={
        <Space>
          <FilePptOutlined style={{ color: '#FF6B6B' }} />
          <span>星火 PPT 课件生成</span>
        </Space>
      }
      extra={<Tag color="orange">讯飞星火</Tag>}
    >
      <div style={{ marginBottom: 16 }}>
        <Text type="secondary">
          基于当前知识点「{topic || '未选择'}」，调用讯飞星火 PPT API 生成专业课件。
          系统会根据学生画像自动调整内容深度。
        </Text>
      </div>

      {loading && (
        <div style={{ marginBottom: 16 }}>
          <Progress percent={progress} status="active" strokeColor="#FF6B6B" />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {phase === 'generating_outline' && '正在生成个性化大纲...'}
            {phase === 'creating_ppt' && '正在调用星火 API 生成课件...'}
            {phase === 'saving_resource' && '正在保存 PPT 文件...'}
            {!phase && '准备中...'}
          </Text>
        </div>
      )}

      <Space wrap>
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          loading={loading}
          onClick={handleGenerate}
          disabled={!topic}
          style={{ background: '#FF6B6B', borderColor: '#FF6B6B' }}
        >
          {loading ? '生成中...' : '生成 PPT 课件'}
        </Button>
      </Space>

      <div style={{ marginTop: 12 }}>
        <Text type="secondary" style={{ fontSize: 11 }}>
          💡 提示：PPT 生成需要 1-3 分钟，生成完成后可在资源列表中下载
        </Text>
      </div>
    </Card>
  )
}
