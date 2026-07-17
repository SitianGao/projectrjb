import { useState, useEffect } from 'react'
import { Button, Drawer, Input, Select, Space, Steps, Tag, Typography, message } from 'antd'
import { ThunderboltOutlined, FileTextOutlined, EditOutlined, CodeOutlined, FilePptOutlined, BranchesOutlined, SoundOutlined } from '@ant-design/icons'
import { generateResources, getTaskStatus } from '../api/resource'
import { useAuth } from '../contexts/AuthContext'

const { Text, Paragraph } = Typography

const TYPE_OPTIONS = [
  { value: 'document', label: '讲义', icon: <FileTextOutlined /> },
  { value: 'exercise', label: '练习题', icon: <EditOutlined /> },
  { value: 'code', label: '代码案例', icon: <CodeOutlined /> },
  { value: 'mindmap', label: '思维导图', icon: <BranchesOutlined /> },
  { value: 'ppt', label: 'PPT 课件', icon: <FilePptOutlined /> },
  { value: 'audio', label: '音频讲解', icon: <SoundOutlined /> },
  { value: 'reading', label: '拓展阅读', icon: <FileTextOutlined /> },
]

const GENERATE_STEPS = [
  { title: '分析学习目标' },
  { title: '检索课程知识库' },
  { title: '生成资源内容' },
  { title: '内容质量检查' },
  { title: '保存资源' },
]

/**
 * Unified resource generation drawer used by:
 * - Global Resource Center (course/stage selectable)
 * - Stage Detail Page (course + stage auto-filled & locked)
 * - Task Page (course + stage + task auto-filled)
 */
export default function ResourceGenerateDrawer({
  visible,
  onClose,
  onGenerated,
  context = {},
}) {
  const { studentId, activeCourse, courses } = useAuth()

  const [topic, setTopic] = useState(context.topic || '')
  const [selectedTypes, setSelectedTypes] = useState(['document', 'exercise'])
  const [difficulty, setDifficulty] = useState('中级')
  const [selectedCourseId, setSelectedCourseId] = useState(context.courseId || activeCourse?.id || '')
  const [selectedStageId, setSelectedStageId] = useState(context.stageId || '')
  const [selectedTaskId, setSelectedTaskId] = useState(context.taskId || '')
  const [requirements, setRequirements] = useState('')

  const [generating, setGenerating] = useState(false)
  const [genStep, setGenStep] = useState(0)
  const [genProgress, setGenProgress] = useState(0)
  const [genError, setGenError] = useState(null)

  const source = context.source || 'global'
  const isStageLocked = source === 'stage' || source === 'task'
  const isCourseLocked = source === 'task'

  useEffect(() => {
    if (visible) {
      setTopic(context.topic || '')
      setSelectedCourseId(context.courseId || activeCourse?.id || '')
      setSelectedStageId(context.stageId || '')
      setSelectedTaskId(context.taskId || '')
      setGenerating(false)
      setGenStep(0)
      setGenError(null)
    }
  }, [visible, context, activeCourse])

  const handleGenerate = async () => {
    if (!topic.trim()) { message.warning('请输入学习主题'); return }
    if (selectedTypes.length === 0) { message.warning('请至少选择一种资源类型'); return }

    setGenerating(true)
    setGenStep(0)
    setGenError(null)

    try {
      const payload = {
        student_id: studentId,
        topic: topic.trim(),
        types: selectedTypes,
        difficulty,
        course_id: selectedCourseId || undefined,
        stage_id: selectedStageId ? Number(selectedStageId) : undefined,
        task_id: selectedTaskId || undefined,
        requirements: requirements.trim() || undefined,
      }

      setGenStep(1)
      const { task_id } = await generateResources(payload)
      if (!task_id) throw new Error('未获取到任务ID')

      for (let i = 0; i < 60; i++) {
        await new Promise((r) => setTimeout(r, 2000))
        const status = await getTaskStatus(task_id)

        if (i < 2) setGenStep(1)
        else if (i < 5) setGenStep(2)
        else setGenStep(3)

        setGenProgress(status.progress || (i * 10))

        if (status.status === 'done') {
          setGenStep(4)
          message.success('资源生成完成！')
          onGenerated?.({ ...payload, task_id, result: status.result })
          onClose()
          return
        }
        if (status.status === 'failed') {
          throw new Error(status.error?.message || status.message || '生成失败')
        }
      }
      throw new Error('生成超时，请稍后重试')
    } catch (err) {
      setGenError(err.message)
      message.error(err.message || '生成失败')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <Drawer
      title="生成学习资源"
      open={visible}
      onClose={onClose}
      width={480}
      styles={{ body: { padding: '20px 24px' } }}
    >
      {generating ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Steps
            current={genStep}
            direction="vertical"
            size="small"
            items={GENERATE_STEPS.map((s, i) => ({
              title: s.title,
              status: i < genStep ? 'finish' : i === genStep ? 'process' : 'wait',
            }))}
          />
          {genError && (
            <div style={{ marginTop: 20 }}>
              <Tag color="red">{genError}</Tag>
              <br />
              <Button onClick={() => { setGenerating(false); setGenError(null) }} style={{ marginTop: 8 }}>
                关闭重试
              </Button>
            </div>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          {/* Source indicator */}
          <Tag color={source === 'stage' ? 'purple' : source === 'task' ? 'blue' : 'default'} style={{ alignSelf: 'flex-start' }}>
            {source === 'stage' ? '为本阶段生成' : source === 'task' ? '为当前任务生成' : '自定义生成'}
          </Tag>

          {/* Course */}
          <div>
            <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}>所属课程</Text>
            <Select
              value={selectedCourseId}
              onChange={setSelectedCourseId}
              disabled={isCourseLocked}
              style={{ width: '100%' }}
              placeholder="选择课程"
              options={(courses || []).map((c) => ({ label: c.title, value: c.id }))}
            />
          </div>

          {/* Stage */}
          <div>
            <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}>所属阶段（可选）</Text>
            <Input
              value={selectedStageId}
              onChange={(e) => setSelectedStageId(e.target.value)}
              disabled={isStageLocked}
              placeholder={isStageLocked ? `阶段${context.stageId}（自动关联）` : '阶段ID'}
              style={{ borderRadius: 8 }}
            />
          </div>

          {/* Topic */}
          <div>
            <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}>学习主题</Text>
            <Input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="如：集合与集合运算"
              style={{ borderRadius: 8 }}
            />
          </div>

          {/* Types */}
          <div>
            <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}>资源类型</Text>
            <Select
              mode="multiple"
              value={selectedTypes}
              onChange={setSelectedTypes}
              style={{ width: '100%' }}
              options={TYPE_OPTIONS}
            />
          </div>

          {/* Difficulty */}
          <div>
            <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}>难度</Text>
            <Select
              value={difficulty}
              onChange={setDifficulty}
              style={{ width: '100%' }}
              options={[
                { label: '初级', value: '初级' },
                { label: '中级', value: '中级' },
                { label: '高级', value: '高级' },
              ]}
            />
          </div>

          {/* Requirements */}
          <div>
            <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}>生成要求（可选）</Text>
            <Input.TextArea
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="如：多使用生活案例"
              rows={2}
              style={{ borderRadius: 8 }}
            />
          </div>

          {/* Actions */}
          <Space style={{ marginTop: 8 }}>
            <Button onClick={onClose} style={{ borderRadius: 8 }}>取消</Button>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={handleGenerate}
              style={{ borderRadius: 8, background: '#6C5CE7', borderColor: '#6C5CE7' }}
            >
              开始生成
            </Button>
          </Space>
        </div>
      )}
    </Drawer>
  )
}
