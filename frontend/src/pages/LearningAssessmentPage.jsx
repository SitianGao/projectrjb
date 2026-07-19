import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button, Result, Select, Skeleton, Typography, message } from 'antd'
import { useAuth } from '../contexts/AuthContext'
import { SCOPE_OPTIONS } from '../services/evaluationService'
import { fetchAssessmentDashboard } from '../services/assessmentMockData'
import AssessmentSummaryCards from '../components/assessment/AssessmentSummaryCards'
import AssessmentRadarChart from '../components/assessment/AssessmentRadarChart'
import AssessmentDiagnosisPanel from '../components/assessment/AssessmentDiagnosisPanel'
import AssessmentTrendChart from '../components/assessment/AssessmentTrendChart'
import AssessmentErrorChart from '../components/assessment/AssessmentErrorChart'
import AssessmentWeakPoints from '../components/assessment/AssessmentWeakPoints'
import './LearningAssessmentPage.css'

const { Title, Text } = Typography

export default function LearningAssessmentPage() {
  const navigate = useNavigate()
  const { courseId: routeCourseId } = useParams()
  const { studentId, activeCourse, courses } = useAuth()

  // 筛选状态
  const [scope, setScope] = useState('last_30_days')
  const [selectedCourseId, setSelectedCourseId] = useState(
    routeCourseId || activeCourse?.id || courses?.[0]?.id
  )
  const courseId = routeCourseId || selectedCourseId || activeCourse?.id || courses?.[0]?.id
  const course = courses?.find((c) => String(c.id) === String(courseId)) || activeCourse

  // 数据状态
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadData = useCallback(async () => {
    if (!courseId) return
    setLoading(true)
    setError(null)
    try {
      const result = await fetchAssessmentDashboard({
        courseId,
        scope,
        studentId: course?.student_id || studentId,
      })
      console.log(6666666,result);
      
      setData(result)
    } catch (err) {
      setError(err.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }, [courseId, scope, studentId, course?.student_id])

  useEffect(() => {
    const timer = setTimeout(loadData, 0)
    return () => clearTimeout(timer)
  }, [loadData])

  // 操作处理
  function handleReview(point) {
    if (point?.actions?.review_resource_id) {
      navigate(`/resources/${point.actions.review_resource_id}`)
    } else {
      navigate('/resources')
    }
  }

  function handlePractice(point) {
    if (point?.actions?.exercise_task_id) {
      message.info(`即将跳转到专项练习：${point.name}`)
      // navigate(`/course/${courseId}/learn/${point.actions.exercise_task_id}`)
    } else {
      message.info(`即将开始${point.name}专项练习`)
    }
  }

  function handleTutor(point) {
    message.info(`正在为你打开 AI 导师，讨论"${point.name}"...`)
    navigate(`/course/${courseId}/chat`)
  }

  // 错误状态
  if (error && !loading) {
    return (
      <div className="assessment-page">
        <div className="assessment-container">
          <Result
            status="error"
            title="学习评估加载失败"
            subTitle={error}
            extra={<Button type="primary" onClick={loadData}>重试</Button>}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="assessment-page">
      <div className="assessment-container">
        {/* 顶部标题区 */}
        <div className="assessment-header">
          <div className="assessment-header-top">
            <div className="assessment-header-info">
              <Title level={2}>学习评估</Title>
            </div>
            <div className="assessment-filters">
              <Select
                value={courseId}
                onChange={setSelectedCourseId}
                style={{ width: 180 }}
                options={(courses || []).map((c) => ({ label: c.title, value: c.id }))}
                placeholder="切换课程"
              />
              <Select
                value={scope}
                onChange={setScope}
                style={{ width: 150 }}
                options={SCOPE_OPTIONS}
              />
            </div>
          </div>
        </div>

        {/* 第一行：概览卡片 */}
        <AssessmentSummaryCards overview={data?.overview} loading={loading} />

        {/* 第二行：雷达图 + 诊断 */}
        <div className="assessment-row-2">
          <AssessmentRadarChart knowledgeMastery={data?.knowledge_mastery} loading={loading} />
          <AssessmentDiagnosisPanel diagnosis={data?.diagnosis} loading={loading} />
        </div>

        {/* 第三行：趋势 + 错误分布 */}
        <div className="assessment-row-3">
          <AssessmentTrendChart trend={data?.trend} loading={loading} />
          <AssessmentErrorChart errorDistribution={data?.error_distribution} loading={loading} />
        </div>

        {/* 第四行：薄弱点诊断 */}
        <div style={{ marginBottom: 22 }}>
          <Title level={4} style={{ margin: '0 0 16px', color: '#111827' }}>
            重点薄弱点诊断
          </Title>
          <AssessmentWeakPoints
            weakPoints={data?.weak_points}
            loading={loading}
            onReview={handleReview}
            onPractice={handlePractice}
            onTutor={handleTutor}
          />
        </div>
      </div>
    </div>
  )
}
