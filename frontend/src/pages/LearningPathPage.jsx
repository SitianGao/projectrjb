import { useState, useEffect } from 'react'
import { Typography, Button, Space, Empty, Card, Tag, message } from 'antd'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import PathTimeline from '../components/PathTimeline'
import ProgressBar from '../components/ProgressBar'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { getStudentPaths, generateLearningPathStream } from '../api/planner'

const { Title, Text } = Typography

/**
 * 将后端 stages 转为 PathTimeline 期望的 nodes
 */
function stagesToNodes(stages, currentStage) {
  return stages.map((stage) => {
    const stageId = stage.stage_id
    let status = 'pending'
    if (stageId < currentStage) status = 'completed'
    else if (stageId === currentStage) status = 'in_progress'

    return {
      id: `stage-${stageId}`,
      title: stage.title,
      description: stage.description || stage.objectives?.join('；'),
      status,
      duration: `${stage.estimated_days || '?'}天`,
      difficulty: stage.difficulty,
      topics: stage.topics,
      tasks: stage.tasks,
    }
  })
}

/**
 * 学习路径页 — 时间线展示 + AI 生成
 */
export default function LearningPathPage() {
  const [currentPath, setCurrentPath] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [genProgress, setGenProgress] = useState(0)
  const [genMessage, setGenMessage] = useState('')
  const [streamContent, setStreamContent] = useState('')
  const [genSteps, setGenSteps] = useState([])

  const studentId = 'demo-student-01'

  useEffect(() => {
    loadPath()
  }, [])

  async function loadPath() {
    setLoading(true)
    try {
      const data = await getStudentPaths(studentId)
      if (data && data.stages) {
        setCurrentPath(data)
      } else {
        setCurrentPath(null)
      }
    } catch {
      setCurrentPath(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerate() {
    setGenerating(true)
    setGenProgress(0)
    setGenMessage('正在分析学生画像...')
    setStreamContent('')
    setGenSteps([
      { key: 'profile', label: '分析学生画像', status: 'process' },
      { key: 'plan', label: '生成学习计划', status: 'wait' },
      { key: 'save', label: '保存路径', status: 'wait' },
    ])

    try {
      const response = await generateLearningPathStream({ student_id: studentId })
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()

          try {
            const parsed = JSON.parse(data)

            switch (parsed.type) {
              case 'start':
                setGenMessage(parsed.message || '开始生成')
                setGenSteps((prev) =>
                  prev.map((s) => (s.key === 'profile' ? { ...s, status: 'finish' } : s))
                )
                setGenSteps((prev) =>
                  prev.map((s) =>
                    s.key === 'plan' ? { ...s, status: 'process' } : s
                  )
                )
                setGenProgress(10)
                break

              case 'delta':
                setStreamContent((prev) => prev + (parsed.content || ''))
                setGenProgress((p) => Math.min(p + 2, 70))
                break

              case 'data':
                if (parsed.data) {
                  setCurrentPath(parsed.data)
                  setGenProgress(85)
                  setGenMessage('路径已生成，正在保存...')
                  setGenSteps((prev) =>
                    prev.map((s) => (s.key === 'plan' ? { ...s, status: 'finish' } : s))
                  )
                  setGenSteps((prev) =>
                    prev.map((s) =>
                      s.key === 'save' ? { ...s, status: 'process' } : s
                    )
                  )
                }
                break

              case 'error':
                message.error(parsed.message || '生成失败')
                break

              case 'done':
                setGenProgress(100)
                setGenMessage('完成！')
                setGenSteps((prev) => prev.map((s) => ({ ...s, status: 'finish' })))
                break
            }
          } catch {
            // skip unparseable lines
          }
        }
      }

      await loadPath()
      message.success('学习路径已生成！')
    } catch (err) {
      console.error('Generate path error:', err)
      message.error('生成失败，请重试')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <LoadingSkeleton type="detail" />

  const nodes = currentPath?.stages
    ? stagesToNodes(currentPath.stages, currentPath.current_stage || 1)
    : []

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>学习路径</Title>
          {currentPath?.goal && (
            <Text type="secondary">目标：{currentPath.goal}</Text>
          )}
          {currentPath?.total_estimated_days && (
            <Tag color="blue" style={{ marginLeft: 8 }}>
              预计 {currentPath.total_estimated_days} 天
            </Tag>
          )}
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadPath}>刷新</Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleGenerate}
            loading={generating}
          >
            生成新路径
          </Button>
        </Space>
      </div>

      {/* 生成进度 */}
      {generating && (
        <Card style={{ marginTop: 16 }}>
          <ProgressBar
            status="running"
            percent={genProgress}
            steps={genSteps}
            message={genMessage || 'AI 正在为你定制学习路径...'}
          />
          {streamContent && (
            <Card
              size="small"
              style={{ marginTop: 12, maxHeight: 200, overflow: 'auto', background: '#fafafa' }}
            >
              <Text style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>
                {streamContent}
              </Text>
            </Card>
          )}
        </Card>
      )}

      {/* 时间线 */}
      <div style={{ marginTop: 24 }}>
        {nodes.length > 0 ? (
          <PathTimeline
            nodes={nodes}
            onNodeClick={(node) => {
              message.info(
                `阶段: ${node.title}\n难度: ${node.difficulty || '未知'}\n时长: ${node.duration}`
              )
            }}
          />
        ) : (
          <Empty description="还没有学习路径，点击上方按钮生成你的第一条路径" />
        )}
      </div>
    </div>
  )
}
