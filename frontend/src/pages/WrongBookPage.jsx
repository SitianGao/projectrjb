import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Alert, Button, Card, Progress, Segmented, Space, Spin, Typography, message,
  Input, Select, Row, Col, Statistic, Breadcrumb,
} from 'antd'
import {
  ArrowLeftOutlined, ReloadOutlined, SearchOutlined,
  ClockCircleOutlined, CheckCircleOutlined, ExclamationCircleOutlined,
  HomeOutlined,
} from '@ant-design/icons'
import WrongQuestionCard from '../components/WrongQuestionCard'
import { createWrongBookResource, getWrongBook, updateWrongQuestion } from '../api/evaluate'
import { getTaskStatus } from '../api/resource'
import { useAuth } from '../contexts/AuthContext'

const { Title, Text, Paragraph } = Typography

export default function WrongBookPage() {
  const navigate = useNavigate()
  const { courseId } = useParams()
  const { studentId, activeCourse, courses } = useAuth()
  const [status, setStatus] = useState('pending')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [reviewing, setReviewing] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [filterCourse, setFilterCourse] = useState(courseId || '')
  const [sortBy, setSortBy] = useState('next_review')
  const [resourceJob, setResourceJob] = useState(null)
  const [generating, setGenerating] = useState(false)

  const currentCourse = useMemo(() => {
    if (courseId) return courses?.find((c) => String(c.id) === String(courseId)) || activeCourse
    if (filterCourse) return courses?.find((c) => String(c.id) === String(filterCourse)) || activeCourse
    return activeCourse
  }, [courseId, filterCourse, courses, activeCourse])

  // Map UI tab to API status. API: unmastered / mastered. We add 'reviewing' / 'pending'.
  const apiStatus = status === 'pending' ? 'unmastered' : status

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const result = await getWrongBook(studentId, apiStatus)
      let list = result?.items || []

      // Course scope filter
      if (currentCourse) {
        list = list.filter((item) =>
          String(item.courseId || item.course_id || '') === String(currentCourse.id) ||
          !item.courseId && !item.course_id
        )
      }
      if (filterCourse && !courseId) {
        list = list.filter((item) =>
          String(item.courseId || item.course_id || '') === String(filterCourse)
        )
      }
      if (keyword) {
        const kw = keyword.toLowerCase()
        list = list.filter((item) =>
          (item.topic || '').toLowerCase().includes(kw) ||
          (item.question || '').toLowerCase().includes(kw)
        )
      }

      // Sort
      if (sortBy === 'next_review') list.sort((a, b) => (a.next_review_at || '').localeCompare(b.next_review_at || ''))
      else if (sortBy === 'wrong_count') list.sort((a, b) => (b.wrong_count || 0) - (a.wrong_count || 0))
      else if (sortBy === 'recent') list.sort((a, b) => (b.last_wrong_at || '').localeCompare(a.last_wrong_at || ''))

      setItems(list)
    } catch (error) {
      message.error(error.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }, [apiStatus, studentId, currentCourse, filterCourse, courseId, keyword, sortBy])

  useEffect(() => { const t = setTimeout(load, 0); return () => clearTimeout(t) }, [load])

  const handleReview = useCallback(async (item, answer) => {
    setReviewing(true)
    try {
      await updateWrongQuestion(item.id, { student_id: studentId, user_answer: answer })
      const result = { is_correct: String(answer).toUpperCase() === String(item.correct_answer).toUpperCase() }
      if (result.is_correct) {
        const newStreak = (item.correct_streak || 0) + 1
        const newStatus = newStreak >= 2 ? 'mastered' : 'reviewing'
        await updateWrongQuestion(item.id, { student_id: studentId, status: newStatus, correct_streak: newStreak })
      } else {
        await updateWrongQuestion(item.id, { student_id: studentId, status: 'reviewing', correct_streak: 0, wrong_count: (item.wrong_count || 0) + 1 })
      }
      load()
      return result
    } catch (err) { message.error(err.message); return { is_correct: false } }
    finally { setReviewing(false) }
  }, [studentId, load])

  const handleManualMaster = useCallback(async (item) => {
    try {
      await updateWrongQuestion(item.id, { student_id: studentId, status: 'mastered', correct_streak: Math.max(item.correct_streak || 0, 2) })
      message.success('已手动标记为掌握')
      load()
    } catch (err) { message.error(err.message) }
  }, [studentId, load])

  const handleRemove = useCallback(async (item) => {
    try {
      await updateWrongQuestion(item.id, { student_id: studentId, status: 'removed' })
      message.success('已移出错题本')
      load()
    } catch (err) { message.error(err.message) }
  }, [studentId, load])

  const pollResourceJob = useCallback(async (taskId) => {
    for (let index = 0; index < 40; index += 1) {
      const next = await getTaskStatus(taskId)
      setResourceJob(next)
      if (next.status === 'done' || next.status === 'failed') return next
      await new Promise((resolve) => setTimeout(resolve, 1000))
    }
    return null
  }, [])

  const handleGenerate = useCallback(async (item, resourceType = 'exercise', variantType = null, selectedItems = null) => {
    const targets = selectedItems || [item]
    if (!targets.length) return
    setGenerating(true)
    try {
      const job = await createWrongBookResource({
        question_ids: targets.map((row) => row.id),
        resource_type: resourceType,
        variant_type: variantType,
      })
      setResourceJob(job)
      pollResourceJob(job.task_id).catch(() => {})
    } catch (error) {
      message.error(error.message || '错题专项资源创建失败')
    } finally {
      setGenerating(false)
    }
  }, [pollResourceJob])

  const stats = useMemo(() => ({
    pending: items.filter((i) => i.status === 'pending' || i.status === 'unmastered').length,
    reviewing: items.filter((i) => i.status === 'reviewing').length,
    mastered: items.filter((i) => i.status === 'mastered').length,
    dueToday: items.filter((i) => i.next_review_at && i.next_review_at <= new Date().toISOString().split('T')[0]).length,
  }), [items])

  const pathUrl = currentCourse ? `/course/${currentCourse.id}/path` : '/journey'
  const tabItems = [
    { key: 'pending', label: `待复习 ${stats.pending}` },
    { key: 'reviewing', label: `复习中 ${stats.reviewing}` },
    { key: 'mastered', label: `已掌握 ${stats.mastered}` },
  ]
  // Map tab key to API status
  useEffect(() => {
    if (status === 'mastered') return
    if (status === 'reviewing') return
  }, [status])

  return (
    <div style={{ minHeight: '100%', background: '#F6F7FB', padding: '20px 24px 48px' }}>
      <div style={{ maxWidth: 1060, margin: '0 auto' }}>
        {/* Breadcrumb */}
        <Breadcrumb style={{ marginBottom: 12, fontSize: 13 }}
          items={[
            { title: <><HomeOutlined style={{ marginRight: 2 }} />学习首页</>, onClick: () => navigate('/home') },
            ...(currentCourse ? [
              { title: currentCourse.title, onClick: () => navigate(`/course/${currentCourse.id}`) },
            ] : []),
            { title: '错题本' },
          ]} />

        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(pathUrl)}
          style={{ marginBottom: 16, paddingLeft: 0 }}>
          返回学习路径
        </Button>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 20 }}>
          <div>
            <Title level={3} style={{ margin: 0, color: '#111827' }}>
              {currentCourse ? `${currentCourse.title} 错题本` : '我的错题本'}
            </Title>
            <Text style={{ color: '#6B7280', fontSize: 13 }}>
              系统会自动收集练习和测评中的错题，并根据复习结果更新掌握状态。
            </Text>
          </div>
          <Space>
            {items.length > 0 && status !== 'mastered' && (
              <Button
                type="primary"
                loading={generating}
                onClick={() => handleGenerate(null, 'exercise', 'targeted_training', items)}
              >
                创建专项训练
              </Button>
            )}
            <Segmented value={status} onChange={setStatus} options={tabItems} />
            <Button icon={<ReloadOutlined />} onClick={load} style={{ borderRadius: 8 }}>刷新</Button>
          </Space>
        </div>

        {/* Statistics */}
        <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ borderRadius: 12, border: '1px solid #E5E7EB', textAlign: 'center' }}>
              <Statistic title="待复习" value={stats.pending} valueStyle={{ color: '#EF4444', fontSize: 24 }}
                prefix={<ExclamationCircleOutlined />} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ borderRadius: 12, border: '1px solid #E5E7EB', textAlign: 'center' }}>
              <Statistic title="今日应复习" value={stats.dueToday} valueStyle={{ color: '#F59E0B', fontSize: 24 }}
                prefix={<ClockCircleOutlined />} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ borderRadius: 12, border: '1px solid #E5E7EB', textAlign: 'center' }}>
              <Statistic title="复习中" value={stats.reviewing} valueStyle={{ color: '#F59E0B', fontSize: 24 }}
                prefix={<ClockCircleOutlined />} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ borderRadius: 12, border: '1px solid #E5E7EB', textAlign: 'center' }}>
              <Statistic title="已掌握" value={stats.mastered} valueStyle={{ color: '#22C55E', fontSize: 24 }}
                prefix={<CheckCircleOutlined />} />
            </Card>
          </Col>
        </Row>

        {resourceJob && (
          <Card size="small" style={{ borderRadius: 12, marginBottom: 16, border: '1px solid #E5E7EB' }}>
            <Alert
              showIcon
              type={resourceJob.status === 'failed' ? 'error' : resourceJob.status === 'done' ? 'success' : 'info'}
              message={resourceJob.message || '正在准备错题专项内容'}
              description={resourceJob.error?.message}
            />
            <Progress percent={resourceJob.progress || 0} strokeColor="#6C5CE7" style={{ marginTop: 12 }} />
            {resourceJob.status === 'done' && resourceJob.result?.learning_route && (
              <Button type="primary" onClick={() => navigate(resourceJob.result.learning_route)}>
                进入专项学习任务
              </Button>
            )}
          </Card>
        )}

        {/* Filters */}
        <div style={{ marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <Input prefix={<SearchOutlined />} placeholder="搜索题目、知识点"
            value={keyword} onChange={(e) => setKeyword(e.target.value)} allowClear
            style={{ width: 240, borderRadius: 8 }} />
          {!courseId && (
            <Select placeholder="全部课程" value={filterCourse} onChange={setFilterCourse} allowClear
              style={{ width: 150, borderRadius: 8 }}
              options={(courses || []).map((c) => ({ label: c.title, value: c.id }))} />
          )}
          <Select value={sortBy} onChange={setSortBy} style={{ width: 140, borderRadius: 8 }}
            options={[
              { label: '下次复习时间', value: 'next_review' },
              { label: '错误次数', value: 'wrong_count' },
              { label: '最近答错', value: 'recent' },
            ]} />
        </div>

        {/* Content */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: 60 }}><Spin tip="正在加载错题..." /></div>
        ) : items.length === 0 ? (
          <Card style={{ borderRadius: 16, textAlign: 'center', padding: 48, border: '1px solid #E5E7EB' }}>
            {status === 'mastered' ? (
              <>
                <CheckCircleOutlined style={{ fontSize: 48, color: '#22C55E', marginBottom: 16 }} />
                <Title level={4} style={{ color: '#111827' }}>还没有已掌握的错题</Title>
                <Paragraph style={{ color: '#6B7280', maxWidth: 400, margin: '0 auto 20px' }}>
                  完成待复习错题，并连续两次答对后，题目会自动进入这里。
                </Paragraph>
                <Button type="primary" onClick={() => setStatus('pending')}
                  style={{ borderRadius: 8, background: '#6C5CE7' }}>去复习待复习错题</Button>
              </>
            ) : (
              <>
                <ExclamationCircleOutlined style={{ fontSize: 48, color: '#D1D5DB', marginBottom: 16 }} />
                <Title level={4} style={{ color: '#111827' }}>暂无错题</Title>
                <Paragraph style={{ color: '#6B7280' }}>继续保持！完成练习和测评后会在此处收集错题。</Paragraph>
              </>
            )}
          </Card>
        ) : (
          <div>
            {items.map((item, idx) => (
              <WrongQuestionCard
                key={item.id || idx}
                item={item}
                onReview={handleReview}
                onManualMaster={handleManualMaster}
                onRemove={handleRemove}
                onGenerate={handleGenerate}
                reviewing={reviewing}
                generating={generating}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
