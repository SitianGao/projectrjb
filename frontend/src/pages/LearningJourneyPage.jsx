import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
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
import StageCard from '../components/StageCard'
import CurrentLearningCard from '../components/CurrentLearningCard'
import ReviewPlanCard from '../components/ReviewPlanCard'
import PathReasonDrawer from '../components/PathReasonDrawer'
import './LearningJourneyPage.css'

// ── helpers ──

function matchResourcesToStage(stage, allResources) {
  const topics = normalizeStringList(stage?.topics)
  if (!allResources?.length) return []
  const exact = allResources.filter(
    (r) => r.stage_id != null && String(r.stage_id) === String(stage?.stage_id),
  )
  if (exact.length) return exact
  if (!topics.length) return []
  return allResources.filter((res) => {
    if (res.stage_id != null) return false
    const resTopic = (res.topic || '').toLowerCase()
    if (!resTopic) return false
    return topics.some((t) => resTopic.includes(t.toLowerCase()) || t.toLowerCase().includes(resTopic))
  })
}

function getStageStatus(stage, currentStage) {
  if (stage?.status === 'completed') return 'completed'
  if (stage?.status === 'active' || stage?.status === 'current') return 'current'
  if (stage?.status === 'locked') return 'locked'
  const cur = Number(currentStage) || 1
  const order = Number(stage.order || stage.stage_id) || 1
  if (order < cur) return 'completed'
  if (order === cur) return 'current'
  return 'locked'
}

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
  const stageListRef = useRef(null)

  // ── Data ──
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pathData, setPathData] = useState(null)
  const [pathMeta, setPathMeta] = useState(null)
  const [resources, setResources] = useState([])
  const [evaluation, setEvaluation] = useState(null)
  const [reviewFeed, setReviewFeed] = useState([])

  // ── UI ──
  const [expandedStageId, setExpandedStageId] = useState(null)
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
      if (!path?.id) {
        setPathData(null)
        setPathMeta(scopedPath)
        setResources([])
        setEvaluation(null)
        setReviewFeed([])
        return
      }
      const [resList, evalReport, feed] = await Promise.all([
        getResources({ student_id: scopedStudentId, path_id: path.id, page_size: 100 }),
        getEvaluation(scopedStudentId).catch(() => null),
        getReviewFeed(scopedStudentId).catch(() => null),
      ])
      setPathData(path)
      setPathMeta(scopedPath)
      setResources(resList?.items || [])
      setEvaluation(evalReport)
      setReviewFeed(feed?.items || [])

      // Set initial expanded / active to current stage
      const current = path.current_stage_id
        || path.stages?.find((stage) => Number(stage.order || stage.stage_id) === Number(path.current_stage || 1))?.stage_id
        || path.stages?.[0]?.stage_id
      setExpandedStageId(current)
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
  const courseStatus = pathMeta?.course_status || (safeAll > 0 && safeDone >= safeAll ? 'completed' : 'learning')
  const nextTask = courseStatus === 'completed'
    ? null
    : currentStageTasks.find((t) => t.status !== 'completed') || null

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
  const handleStageClick = useCallback((stage, stageId) => {
    setActiveStageId(stageId)
    setExpandedStageId((prev) => prev === stageId ? null : stageId)
    // Scroll to stage
    setTimeout(() => {
      document.getElementById(`stage-${stageId}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  }, [])

  const stageBaseUrl = currentCourse?.id ? `/course/${currentCourse.id}/stage` : '/stage'
  const handleRegenerate = useCallback(() => navigate('/profile', { state: { startChat: true } }), [navigate])

  const handleContinueLearning = useCallback(() => {
    const route = pathMeta?.continue_target?.route
    if (route) {
      navigate(route)
      return
    }
    continueLearning(currentCourse?.id)
  }, [continueLearning, currentCourse, navigate, pathMeta])

  const handleGoStageDetail = useCallback((stage) => {
    if (!stage) return
    navigate(`${stageBaseUrl}/${stage.stage_id}?pathId=${encodeURIComponent(pathData?.id || '')}`, {
      state: { stage, pathId: pathData?.id, pathData },
    })
  }, [navigate, pathData, stageBaseUrl])

  // ── Render states ──
  if (loading) return <div style={{ height: '100%', background: 'var(--bg-page)' }}><LoadingSkeleton type="detail" /></div>
  if (error) {
    return (
      <div style={{ maxWidth: 500, margin: '60px auto', background: 'var(--bg-page)', padding: 24 }}>
        <Result status="error" title="学习路径加载失败" subTitle={error}
          extra={[
            <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={loadAllData}>重新加载</Button>,
            <Button key="courses" onClick={() => navigate('/courses')}>返回课程列表</Button>,
          ]} />
      </div>
    )
  }
  if (!stages.length) {
    return (
      <div style={{ maxWidth: 500, margin: '60px auto', background: 'var(--bg-page)', padding: 24 }}>
        <Empty description="暂未生成学习路径">
          <Button type="primary" onClick={() => navigate(currentCourse?.id ? `/course/${currentCourse.id}/profile/setup` : '/courses')} style={{ borderRadius: 8 }}>生成学习路径</Button>
        </Empty>
      </div>
    )
  }

  const courseName = currentCourse?.title || pathData?.course_title || '人工智能'

  return (
    <div style={{
      minHeight: '100%', background: 'var(--bg-page)',
      padding: '20px 24px 48px',
    }}>
      <div style={{ maxWidth: 1440, margin: '0 auto', minWidth: 0 }}>

        {/* 1. Header */}
        <CoursePathHeader
          courseName={courseName}
          courseId={currentCourse?.id}
          currentStageTitle={currentStageData?.title || ''}
          currentStageId={currentStageNum}
          totalStages={stages.length}
          completedTasks={safeDone}
          totalTasks={safeAll}
          masteryPercent={mastery}
          onRegenerate={handleRegenerate}
          onContinueStage={handleContinueLearning}
        />

        {/* 2. Compact path overview */}
        <PathOverview
          stages={stages}
          currentStage={currentStageNum}
          activeStageId={activeStageId}
          onStageClick={handleStageClick}
        />

        {/* 3. Main content: left stages + right panels */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr) 380px',
          gap: 24,
          alignItems: 'start',
        }}>
          {/* Left: Stage cards */}
          <div style={{ minWidth: 0 }} ref={stageListRef}>
            {stages.map((stage, index) => {
              const sid = stage.stage_id
              const status = getStageStatus(stage, currentStageNum)
              const stageRes = matchResourcesToStage(stage, resources)
              return (
                <div key={sid} id={`stage-${sid}`}>
                  <StageCard
                    stage={stage}
                    status={status}
                    stageIndex={stage.order || index + 1}
                    resources={stageRes}
                    expanded={expandedStageId === sid}
                    onToggle={() => handleStageClick(stage, sid)}
                    onContinue={handleContinueLearning}
                    onViewDetail={handleGoStageDetail}
                    onTaskOpen={(task) => navigate(`/course/${currentCourse.id}/learn/${encodeURIComponent(task.task_id || task.id)}`)}
                  />
                </div>
              )
            })}

            {/* "Why this path" link */}
            <Button type="link" onClick={() => setReasonDrawer(true)}
              style={{ color: '#6C5CE7', padding: 0, fontSize: 13, marginTop: 8 }}>
              查看生成依据
            </Button>
          </div>

          {/* Right: Current learning + Review plans */}
          <div style={{ minWidth: 0, display: 'flex', flexDirection: 'column', gap: 20 }}>
            <CurrentLearningCard
              stageTitle={currentStageData?.title || ''}
              stageId={currentStageNum}
              nextTaskTitle={nextTask?.description || nextTask?.title || '阅读核心讲义'}
              estimatedMinutes={Math.round((nextTask?.estimated_hours || 0.3) * 60)}
              completedTasks={currentCompleted}
              totalTasks={currentStageTasks.length}
              continueLabel={courseStatus === 'completed' ? '查看学习总结' : '继续学习'}
              onContinue={handleContinueLearning}
              onViewResources={() => currentStageData && navigate(`${stageBaseUrl}/${currentStageData.stage_id}?pathId=${encodeURIComponent(pathData?.id || '')}`, { state: { stage: currentStageData, pathId: pathData?.id, pathData } })}
            />
            <ReviewPlanCard
              plans={scopedPlans}
              maxItems={3}
              onStartReview={() => { /* navigate to review */ }}
            />
          </div>
        </div>
      </div>

      {/* ═══ Drawers & Modals ═══ */}
      <PathReasonDrawer visible={reasonDrawer} onClose={() => setReasonDrawer(false)} pathData={pathData} />

    </div>
  )
}
