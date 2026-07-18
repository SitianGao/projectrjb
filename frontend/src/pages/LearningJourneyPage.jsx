import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Button, Empty, message, Result, Spin, Modal } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { getLearningPath, getLearningPathById } from '../api/planner'
import { getResources, getResource } from '../api/resource'
import { getEvaluation, getReviewFeed, getWrongBook } from '../api/evaluate'
import { useLearningBehavior } from '../hooks/useLearningBehavior'
import { normalizeStringList, normalizeTasks } from '../utils/stageUtils'
import { safeProgress, dedupeTasks, dedupeResources, scopedReviewPlans } from '../utils/safeClamp'
import { useAuth } from '../contexts/AuthContext'
import { useContinueLearning } from '../hooks/useContinueLearning'
import LoadingSkeleton from '../components/LoadingSkeleton'
import MarkdownRenderer from '../components/MarkdownRenderer'
import QuizCard from '../components/QuizCard'
import CoursePathHeader from '../components/CoursePathHeader'
import PathOverview from '../components/PathOverview'
import StageCard from '../components/StageCard'
import StageDetailDrawer from '../components/StageDetailDrawer'
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
  const cur = currentStage || 1
  const id = stage.stage_id
  if (id < cur) return 'completed'
  if (id === cur) return 'current'
  return 'locked'
}

function parseExerciseContent(resource) {
  if (resource?.type !== 'exercise' || !resource.content) return []
  try {
    const parsed = typeof resource.content === 'string' ? JSON.parse(resource.content) : resource.content
    if (!Array.isArray(parsed)) return []
    return parsed.map((item, i) => {
      const options = Array.isArray(item.options)
        ? item.options.map((opt, oi) => {
          if (typeof opt === 'object') return { key: String(opt.key || opt.label || String.fromCharCode(65 + oi)).toUpperCase(), content: opt.content || opt.text || opt.value || '' }
          const text = String(opt)
          const m = text.match(/^([A-D])[.、:：]\s*(.*)$/i)
          return { key: m ? m[1].toUpperCase() : String.fromCharCode(65 + oi), content: m ? m[2] : text }
        }) : []
      return { ...item, id: String(item.id || `${resource.id}-q${i + 1}`), options, answer: String(item.answer || '').toUpperCase(), difficulty: item.difficulty || 'medium' }
    }).filter((q) => q.question && q.options.length > 0 && q.answer)
  } catch { return [] }
}

// ═══════════════════════════════════════════════
// Main Page
// ═══════════════════════════════════════════════

export default function LearningJourneyPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { studentId, activeCourse, courses } = useAuth()
  const { continueLearning } = useContinueLearning()
  const pathId = new URLSearchParams(location.search).get('pathId')
  const stageListRef = useRef(null)

  // ── Data ──
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pathData, setPathData] = useState(null)
  const [resources, setResources] = useState([])
  const [evaluation, setEvaluation] = useState(null)
  const [reviewFeed, setReviewFeed] = useState([])
  const [wrongBookCount, setWrongBookCount] = useState(0)

  // ── UI ──
  const [expandedStageId, setExpandedStageId] = useState(null)
  const [activeStageId, setActiveStageId] = useState(null)
  const [detailStage, setDetailStage] = useState(null)
  const [reasonDrawer, setReasonDrawer] = useState(false)
  const [selectedResource, setSelectedResource] = useState(null)
  const [resourceModalVisible, setResourceModalVisible] = useState(false)
  const [completing, setCompleting] = useState(false)
  const [resourceError, setResourceError] = useState(null)

  const { trackView, trackComplete, trackExerciseAnswer } = useLearningBehavior(studentId, (report, adaptation) => {
    if (report) setEvaluation(report)
    if (adaptation?.learning_path?.stages?.length) setPathData(adaptation.learning_path)
    if (adaptation?.review_resources?.length) {
      setResources((cur) => { const m = new Map(cur.map((r) => [r.id, r])); adaptation.review_resources.forEach((r) => m.set(r.id, r)); return [...m.values()] })
    }
  })

  // ── Current course context ──
  const currentCourse = useMemo(() => {
    if (activeCourse) return activeCourse
    return courses?.[0] || null
  }, [activeCourse, courses])

  // ── Load ──
  const loadAllData = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      if (!studentId) throw new Error('当前课程上下文不存在')
      const path = pathId ? await getLearningPathById(studentId, pathId) : await getLearningPath(studentId)
      if (!path?.id) throw new Error('还没有生成学习路径')
      const [resList, evalReport, feed, wb] = await Promise.all([
        getResources({ student_id: studentId, path_id: path.id, page_size: 100 }),
        getEvaluation(studentId).catch(() => null),
        getReviewFeed(studentId).catch(() => null),
        getWrongBook(studentId).catch(() => null),
      ])
      setPathData(path)
      setResources(resList?.items || [])
      setEvaluation(evalReport)
      setReviewFeed(feed?.items || [])
      setWrongBookCount(wb?.total || 0)

      // Set initial expanded / active to current stage
      const cur = path.current_stage || 1
      setExpandedStageId(cur)
      setActiveStageId(cur)
    } catch (err) { setError(err.message || '加载失败') }
    finally { setLoading(false) }
  }, [studentId, pathId])

  useEffect(() => { loadAllData() }, [loadAllData])

  // ── Derived ──
  const stages = useMemo(() => pathData?.stages || [], [pathData])
  const currentStageNum = pathData?.current_stage || 1
  const currentStageData = useMemo(() => stages.find((s) => s.stage_id === currentStageNum), [stages, currentStageNum])

  const allTasksDeduped = useMemo(() => dedupeTasks(stages.flatMap((s) => normalizeTasks(s.tasks))), [stages])
  const totalCompleted = allTasksDeduped.filter((t) => t.status === 'completed').length
  const { completed: safeDone, total: safeAll, percent: overallPct } = safeProgress(totalCompleted, allTasksDeduped.length)

  const currentStageResources = useMemo(() => matchResourcesToStage(currentStageData, resources), [currentStageData, resources])
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
  const handleStageClick = useCallback((stage, stageId) => {
    setActiveStageId(stageId)
    setExpandedStageId((prev) => prev === stageId ? null : stageId)
    // Scroll to stage
    setTimeout(() => {
      document.getElementById(`stage-${stageId}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  }, [])

  const stageBaseUrl = currentCourse?.id ? `/course/${currentCourse.id}/stage` : '/stage'
  const wrongbookUrl = currentCourse?.id ? `/course/${currentCourse.id}/wrongbook` : '/wrong-book'

  const handleViewDetail = useCallback((stage) => setDetailStage(stage), [])
  const handleRegenerate = useCallback(() => navigate('/profile', { state: { startChat: true } }), [navigate])

  const handleContinueLearning = useCallback(() => {
    continueLearning(currentCourse?.id)
  }, [continueLearning, currentCourse])

  const handleGoStageDetail = useCallback((stage) => {
    if (!stage) return
    navigate(`${stageBaseUrl}/${stage.stage_id}?pathId=${encodeURIComponent(pathData?.id || '')}`, {
      state: { stage, pathId: pathData?.id, pathData },
    })
  }, [navigate, pathData, stageBaseUrl])

  const handleResourceClick = useCallback(async (resource) => {
    setResourceError(null); setSelectedResource(resource); setResourceModalVisible(true)
    trackView(resource)
    if (resource.content) return
    try {
      const detail = await getResource(resource.id)
      if (detail) setSelectedResource({ ...resource, ...detail })
    } catch (err) { setResourceError(err.message || '加载失败') }
  }, [trackView])

  const handleCompleteResource = useCallback(async () => {
    if (!selectedResource) return
    setCompleting(true)
    try { await trackComplete(selectedResource); message.success('已更新'); setResourceModalVisible(false); setSelectedResource(null) }
    catch (err) { message.error('记录失败') }
    finally { setCompleting(false) }
  }, [selectedResource, trackComplete])

  const handleExerciseAnswered = useCallback(async (resource, quiz, selected, isCorrect) => {
    try {
      const r = await trackExerciseAnswer(resource, quiz, selected, isCorrect)
      if (r?.added_to_wrong_book) { setWrongBookCount((c) => c + 1); message.warning('已加入错题本') }
      else message.success('已保存')
      const f = await getReviewFeed(studentId).catch(() => null)
      if (f?.items) setReviewFeed(f.items)
    } catch (err) { message.error(err.message) }
  }, [trackExerciseAnswer, studentId])

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

  const courseName = pathData?.goal || currentCourse?.title || '人工智能'

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
            {stages.map((stage, idx) => {
              const sid = stage.stage_id
              const status = getStageStatus(stage, currentStageNum)
              const stageRes = matchResourcesToStage(stage, resources)
              return (
                <div key={sid} id={`stage-${sid}`}>
                  <StageCard
                    stage={stage}
                    status={status}
                    stageIndex={sid}
                    resources={stageRes}
                    expanded={expandedStageId === sid}
                    onToggle={() => handleStageClick(stage, sid)}
                    onContinue={handleContinueLearning}
                    onViewDetail={handleGoStageDetail}
                  />
                </div>
              )
            })}

            {/* "Why this path" link */}
            <Button type="link" onClick={() => setReasonDrawer(true)}
              style={{ color: '#6C5CE7', padding: 0, fontSize: 13, marginTop: 8 }}>
              为什么这样规划？
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
              onContinue={handleContinueLearning}
              onViewResources={() => currentStageData && navigate(`${stageBaseUrl}/${currentStageData.stage_id}?pathId=${encodeURIComponent(pathData?.id || '')}`, { state: { stage: currentStageData, pathId: pathData?.id, pathData } })}
            />
            <ReviewPlanCard
              plans={scopedPlans}
              maxItems={3}
              onStartReview={(item) => { /* navigate to review */ }}
            />
          </div>
        </div>
      </div>

      {/* ═══ Drawers & Modals ═══ */}
      <StageDetailDrawer
        stage={detailStage}
        resources={detailStage ? matchResourcesToStage(detailStage, resources) : []}
        visible={!!detailStage}
        onClose={() => setDetailStage(null)}
        onContinue={handleContinueLearning}
        onResourceClick={handleResourceClick}
      />
      <PathReasonDrawer visible={reasonDrawer} onClose={() => setReasonDrawer(false)} pathData={pathData} />

      {/* Resource detail modal */}
      <Modal
        title={selectedResource?.title || '资源详情'}
        open={resourceModalVisible}
        onCancel={() => { setResourceModalVisible(false); setSelectedResource(null); setResourceError(null) }}
        footer={resourceError ? [
          <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={async () => { setResourceError(null); try { const d = await getResource(selectedResource.id); if (d) setSelectedResource({ ...selectedResource, ...d }) } catch (e) { setResourceError(e.message) } }}>重试</Button>,
        ] : selectedResource ? [
          <Button key="close" onClick={() => { setResourceModalVisible(false); setSelectedResource(null) }}>关闭</Button>,
          <Button key="complete" type="primary" onClick={handleCompleteResource} loading={completing} style={{ borderRadius: 8, background: '#6C5CE7' }}>完成学习</Button>,
        ] : null}
        width={720}
        styles={{ body: { maxHeight: '65vh', overflow: 'auto', padding: '20px 28px' } }}
      >
        {resourceError ? <Result status="error" title="加载失败" subTitle={resourceError} /> :
         !selectedResource ? null :
         parseExerciseContent(selectedResource).length > 0 ? (
           <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
             {parseExerciseContent(selectedResource).map((q) => (
               <QuizCard key={q.id} quiz={q} onAnswered={(_, isCorrect, sel) => handleExerciseAnswered(selectedResource, q, sel, isCorrect)} />
             ))}
           </div>
         ) : selectedResource.content ? <MarkdownRenderer content={selectedResource.content} /> :
         <Empty description="暂无内容" />
        }
      </Modal>
    </div>
  )
}
