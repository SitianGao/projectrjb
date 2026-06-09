import { useState, useEffect } from 'react'
import { Typography, Button, Space, Empty, Card } from 'antd'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import PathTimeline from '../components/PathTimeline'
import ProgressBar from '../components/ProgressBar'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { getStudentPaths, generateLearningPathStream } from '../api/planner'
import { useTaskStatus } from '../hooks/useTaskStatus'

const { Title, Text } = Typography

/**
 * 学习路径页 — 时间线展示 + AI 生成
 */
export default function LearningPathPage() {
  const [paths, setPaths] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [genProgress, setGenProgress] = useState(0)
  const [genSteps, setGenSteps] = useState([])

  const studentId = 'demo-student-01'

  useEffect(() => {
    loadPaths()
  }, [])

  async function loadPaths() {
    setLoading(true)
    try {
      const data = await getStudentPaths(studentId)
      setPaths(Array.isArray(data) ? data : data?.paths || [])
    } catch {
      // 模拟数据
      setPaths([
        {
          id: '1',
          nodes: [
            { id: 'n1', title: '二次函数基础', description: '掌握 y=ax²+bx+c 的图像与性质', status: 'completed', duration: '2h' },
            { id: 'n2', title: '函数与方程', description: '学会用函数图像解方程', status: 'completed', duration: '1.5h' },
            { id: 'n3', title: '不等式与函数', description: '理解二次不等式与函数的关系', status: 'in_progress', duration: '2h' },
            { id: 'n4', title: '函数综合应用', description: '综合运用函数知识解决实际问题', status: 'pending', duration: '3h' },
            { id: 'n5', title: '章节测验', description: '完成单元测试，评估掌握程度', status: 'locked', duration: '1h' },
          ],
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerate() {
    setGenerating(true)
    setGenProgress(0)
    setGenSteps([
      { key: 'analyze', label: '分析学生画像', status: 'process' },
      { key: 'plan', label: '生成学习计划', status: 'wait' },
      { key: 'resources', label: '匹配学习资源', status: 'wait' },
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
          if (data === '[DONE]') continue

          try {
            const parsed = JSON.parse(data)
            if (parsed.progress !== undefined) setGenProgress(parsed.progress)
            if (parsed.stage) {
              setGenSteps((prev) =>
                prev.map((s, i) =>
                  i === prev.findIndex((x) => x.key === parsed.stage)
                    ? { ...s, status: 'process' }
                    : i < prev.findIndex((x) => x.key === parsed.stage)
                      ? { ...s, status: 'finish' }
                      : s,
                ),
              )
            }
          } catch { /* skip */ }
        }
      }

      // 完成后刷新列表
      setGenProgress(100)
      setGenSteps((prev) => prev.map((s) => ({ ...s, status: 'finish' })))
      await loadPaths()
    } catch (err) {
      console.error('Generate path error:', err)
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <LoadingSkeleton type="detail" />

  const currentPath = paths[0]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0 }}>学习路径</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadPaths}>刷新</Button>
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
            message="AI 正在为你定制学习路径..."
          />
        </Card>
      )}

      {/* 时间线 */}
      <div style={{ marginTop: 24 }}>
        {currentPath ? (
          <PathTimeline
            nodes={currentPath.nodes}
            onNodeClick={(node) => console.log('Node clicked:', node)}
          />
        ) : (
          <Empty description="还没有学习路径，点击上方按钮生成你的第一条路径" />
        )}
      </div>
    </div>
  )
}
