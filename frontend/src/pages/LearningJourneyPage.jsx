import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate, useLocation, useParams } from 'react-router-dom'
import { Button, Empty, Result } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { getLearningPathById } from '../api/planner'
import { getCourseLearningPath } from '../api/courseLearning'
import { getResources } from '../api/resource'
import { getEvaluation, getReviewFeed } from '../api/evaluate'
import { normalizeStringList, normalizeTasks } from '../utils/stageUtils'
import { safeProgress, dedupeTasks, scopedReviewPlans } from '../utils/safeClamp'
import { useAuth } from '../contexts/AuthContext'
import { useContinueLearning } from '../hooks/useContinueLearning'
import LoadingSkeleton from '../components/LoadingSkeleton'
import CoursePathHeader from '../components/CoursePathHeader'
import PathOverview from '../components/PathOverview'
import ReviewPlanCard from '../components/ReviewPlanCard'
import PathReasonDrawer from '../components/PathReasonDrawer'
import './LearningJourneyPage.css'


// ═══════════════════════════════════════════════
// Main Page
// ═══════════════════════════════════════════════

export default function LearningJourneyPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { courseId } = useParams()
  const { studentId, activeCourse, courses } = useAuth()
  const { continueLearning } = useContinueLearning()
  const pathId = new URLSearchParams(location.search).get('pathId')

  // ── Data ──
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pathData, setPathData] = useState(null)
  const [resources, setResources] = useState([])
  const [evaluation, setEvaluation] = useState(null)
  const [reviewFeed, setReviewFeed] = useState([])

  // ── UI ──
  const [activeStageId, setActiveStageId] = useState(null)
  const [reasonDrawer, setReasonDrawer] = useState(false)
  // ── Current course context ──
  const currentCourse = useMemo(() => {
    const routeCourse = courses?.find((course) => String(course.id) === String(courseId))
    if (routeCourse) return routeCourse
    if (activeCourse) return activeCourse
    return courses?.[0] || null
  }, [activeCourse, courseId, courses])

  // ── Load ──
  const loadAllData = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const scopedStudentId = currentCourse?.student_id || studentId
      if (!currentCourse?.id || !scopedStudentId) throw new Error('当前课程上下文不存在')
      const scopedPath = pathId
        ? await getLearningPathById(scopedStudentId, pathId)
        : await getCourseLearningPath(currentCourse.id)
      const path = scopedPath?.path || scopedPath
      if (!path?.id) throw new Error('还没有生成学习路径')
      const [resList, evalReport, feed] = await Promise.all([
        getResources({ student_id: scopedStudentId, path_id: path.id, page_size: 100 }),
        getEvaluation(scopedStudentId).catch(() => null),
        getReviewFeed(scopedStudentId).catch(() => null),
      ])
      setPathData(path)
      setResources(resList?.items || [])
      setEvaluation(evalReport)
      setReviewFeed(feed?.items || [])

      // Set active to current stage
      const current = path.current_stage_id
        || path.stages?.find((stage) => Number(stage.order || stage.stage_id) === Number(path.current_stage || 1))?.stage_id
        || path.stages?.[0]?.stage_id
      setActiveStageId(current)
    } catch (err) { setError(err.message || '加载失败') }
    finally { setLoading(false) }
  }, [currentCourse, pathId, studentId])

  useEffect(() => {
    const timer = window.setTimeout(() => loadAllData(), 0)
    return () => window.clearTimeout(timer)
  }, [loadAllData])

  // ── Derived ──
  const stages = useMemo(() => pathData?.stages || [], [pathData])
  const currentStageNum = pathData?.current_stage || 1
  const currentStageData = useMemo(
    () => stages.find((s) => String(s.stage_id) === String(pathData?.current_stage_id))
      || stages.find((s) => Number(s.order || s.stage_id) === Number(currentStageNum))
      || stages[0],
    [pathData?.current_stage_id, stages, currentStageNum],
  )

  const allTasksDeduped = useMemo(() => dedupeTasks(stages.flatMap((s) => normalizeTasks(s.tasks))), [stages])
  const totalCompleted = allTasksDeduped.filter((t) => t.status === 'completed').length
  const { completed: safeDone, total: safeAll } = safeProgress(totalCompleted, allTasksDeduped.length)

  const currentStageTasks = useMemo(() => normalizeTasks(currentStageData?.tasks), [currentStageData])
  const currentCompleted = currentStageTasks.filter((t) => t.status === 'completed').length
  const nextTask = currentStageTasks.find((t) => t.status !== 'completed') || currentStageTasks[0]

  // Course-scoped review plans
  const validTopics = useMemo(() => {
    const s = new Set()
    stages.forEach((st) => normalizeStringList(st.topics).forEach((t) => s.add(t)))
    return s
  }, [stages])

  const scopedPlans = useMemo(() => {
    if (!reviewFeed.length) {
      const raw = evaluation?.reviewPlan || evaluation?.review_plan || []
      return scopedReviewPlans(raw, currentCourse, validTopics)
    }
    return scopedReviewPlans(reviewFeed, currentCourse, validTopics)
  }, [reviewFeed, evaluation, currentCourse, validTopics])

  // Mastery from evaluation
  const mastery = useMemo(() => {
    const score = evaluation?.overallScore || evaluation?.overall_score
    return score != null ? Math.round(score) : 0
  }, [evaluation])

  // ── Handlers ──
  const handleGoStageDetail = useCallback((stage) => {
    if (!stage || !currentCourse?.id) return
    const tasks = normalizeTasks(stage.tasks)
    const firstTask = tasks[0]
    if (firstTask?.task_id) {
      navigate(`/course/${currentCourse.id}/learn/${firstTask.task_id}`)
    } else {
      navigate(`/course/${currentCourse.id}/stage/${stage.stage_id}`)
    }
  }, [navigate, currentCourse])

  const handleStageClick = useCallback((stage, stageId) => {
    setActiveStageId(stageId || stage?.stage_id)
    handleGoStageDetail(stage)
  }, [handleGoStageDetail])

  const handleContinueLearning = useCallback(() => {
    continueLearning(currentCourse?.id)
  }, [continueLearning, currentCourse])

  // ── Render states ──
  if (loading) return <div style={{ height: '100%', background: 'var(--bg-page)' }}><LoadingSkeleton type="detail" /></div>
  if (error) {
    return (
      <div style={{ maxWidth: 500, margin: '60px auto', background: 'var(--bg-page)', padding: 24 }}>
        <Result status="error" title="学习路径加载失败" subTitle={error}
          extra={<Button type="primary" icon={<ReloadOutlined />} onClick={loadAllData}>重新加载</Button>} />
      </div>
    )
  }
  if (!stages.length) {
    return (
      <div style={{ maxWidth: 500, margin: '60px auto', background: 'var(--bg-page)', padding: 24 }}>
        <Empty description="暂未生成学习路径">
          <Button type="primary" onClick={() => navigate('/profile', { state: { startChat: true } })} style={{ borderRadius: 8 }}>生成学习路径</Button>
        </Empty>
      </div>
    )
  }

  const courseName = currentCourse?.title || pathData?.course_title || '人工智能'

  return (
    <div className="lj-page">
      <div className="lj-container">
        {/* Header */}
        <CoursePathHeader
          courseName={courseName}
          courseId={currentCourse?.id}
        />

        {/* Path overview */}
        <PathOverview
          stages={stages}
          currentStage={currentStageNum}
          activeStageId={activeStageId}
          onStageClick={handleStageClick}
        />

        {/* Review plans */}
        <ReviewPlanCard
          plans={scopedPlans}
          maxItems={3}
          onStartReview={() => { /* navigate to review */ }}
        />
      </div>

      {/* ═══ Drawers & Modals ═══ */}
      <PathReasonDrawer visible={reasonDrawer} onClose={() => setReasonDrawer(false)} pathData={pathData} />

    </div>
  )
}
