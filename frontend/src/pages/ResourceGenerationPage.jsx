import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { message, Space, Button } from 'antd'
import { ReloadOutlined, HomeOutlined } from '@ant-design/icons'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { generateResources, getTaskStatus } from '../api/resource'
import { useTaskStatus } from '../hooks/useTaskStatus'
import GenerationBackButton from '../components/generation/GenerationBackButton'
import GenerationProgressDots from '../components/generation/GenerationProgressDots'
import GenerationStepCard from '../components/generation/GenerationStepCard'
import GenerationAgentLogCarousel from '../components/generation/GenerationAgentLogCarousel'
import GenerationAgentPopover from '../components/generation/GenerationAgentPopover'
import GenerationErrorState from '../components/generation/GenerationErrorState'
import {
  GENERATION_STEPS,
  getCurrentStepIndex,
  getStepProgress,
} from '../components/generation/generationSteps'
import './ResourceGenerationPage.css'

// Keep the original RESOURCE_TYPES for the API call
const RESOURCE_TYPES = [
  { key: 'document', name: '专业课程讲解文档' },
  { key: 'mindmap',  name: '知识点思维导图' },
  { key: 'exercise', name: '不同类型练习题目' },
  { key: 'reading',  name: '拓展阅读材料' },
  { key: 'code',     name: '代码类实操案例' },
]

// ==================== 主组件 ====================

export default function ResourceGenerationPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [generationSession, setGenerationSession] = useState(() => {
    if (location.state?.studentId) return location.state
    try {
      const saved = sessionStorage.getItem('journeyGenerationSession')
      return saved ? JSON.parse(saved) : {}
    } catch {
      return {}
    }
  })
  const { studentId, courseId, pathId, stageId, topic, taskId: savedTaskId } = generationSession

  const redirectedRef = useRef(false)
  const initiatedRef = useRef(false)

  const [generateError, setGenerateError] = useState(null)
  const [generating, setGenerating] = useState(false)

  const persistSession = useCallback((updates) => {
    setGenerationSession((current) => {
      const next = { ...current, ...updates }
      sessionStorage.setItem('journeyGenerationSession', JSON.stringify(next))
      return next
    })
  }, [])

  // wrap getTaskStatus: backend returns 'done', useTaskStatus expects 'completed'
  const fetchTaskStatus = useCallback(async (taskId) => {
    const raw = await getTaskStatus(taskId)
    return { ...raw, status: raw.status === 'done' ? 'completed' : raw.status }
  }, [])

  const {
    status: taskStatus,
    error: pollError,
    progress,
    taskMessage,
    startPolling,
    reset: resetPolling,
  } = useTaskStatus(fetchTaskStatus, { interval: 2000 })

  // ── No nav state: redirect home ──
  useEffect(() => {
    if (redirectedRef.current) return
    if (!studentId || !pathId || !topic) {
      redirectedRef.current = true
      message.warning('缺少生成参数，请返回首页重新开始')
      navigate('/home', { replace: true })
    }
  }, [studentId, pathId, topic, navigate])

  // ── Initiate resource generation ──
  useEffect(() => {
    if (!studentId || !pathId || !topic) return
    if (initiatedRef.current) return
    initiatedRef.current = true

    async function initiate() {
      setGenerating(true)
      setGenerateError(null)
      try {
        if (savedTaskId) {
          startPolling(savedTaskId)
          return
        }
        const result = await generateResources({
          student_id: studentId,
          topic,
          path_id: pathId,
          stage_id: stageId,
          types: RESOURCE_TYPES.map((r) => r.key),
        })
        const taskId = result?.task_id
        if (!taskId) throw new Error('资源生成任务创建失败')
        persistSession({ taskId })
        startPolling(taskId)
      } catch (err) {
        setGenerateError(err.message || '资源生成请求失败')
      } finally {
        setGenerating(false)
      }
    }

    initiate()
  }, [studentId, pathId, stageId, topic, savedTaskId, startPolling, persistSession])

  // ── Auto-navigate on completion ──
  useEffect(() => {
    if (taskStatus === 'completed') {
      sessionStorage.removeItem('journeyGenerationSession')
      const timer = setTimeout(() => {
        navigate(courseId ? `/course/${courseId}` : '/home', { replace: true })
      }, 2500)
      return () => clearTimeout(timer)
    }
  }, [courseId, taskStatus, navigate])

  // ── Loading / no state ──
  if (!studentId || !pathId || !topic) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F6F7FB' }}>
        <LoadingSkeleton type="detail" />
      </div>
    )
  }

  // ── generateResources() API call failed ──
  if (generateError) {
    return (
      <GenerationErrorState
        title="资源生成启动失败"
        subTitle={generateError}
        onRetry={() => {
          setGenerateError(null)
          initiatedRef.current = false
          resetPolling()
          persistSession({ taskId: undefined })
        }}
        onGoHome={() => navigate('/home', { replace: true })}
      />
    )
  }

  // ── Task poll error ──
  if (taskStatus === 'failed' || pollError) {
    return (
      <GenerationErrorState
        title="资源生成失败"
        subTitle={pollError || '任务执行过程中出现错误'}
        onRetry={() => {
          setGenerateError(null)
          if (pollError) resetPolling()
          initiatedRef.current = false
          persistSession({ taskId: undefined })
        }}
        onGoHome={() => navigate('/home', { replace: true })}
      />
    )
  }

  // ── Initial loading ──
  if (generating || taskStatus === 'idle' || taskStatus === 'pending') {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F6F7FB' }}>
        <LoadingSkeleton type="detail" />
      </div>
    )
  }

  // ═══════════════════════════════════════════════════════════
  //  MAIN UI — new immersive generation process design
  // ═══════════════════════════════════════════════════════════

  const overallPercent = taskStatus === 'completed' ? 100 : Math.max(progress, 0)
  const currentStepIndex = taskStatus === 'completed'
    ? GENERATION_STEPS.length - 1
    : getCurrentStepIndex(overallPercent)
  const currentStep = GENERATION_STEPS[currentStepIndex]
  const stepProgress = getStepProgress(overallPercent, currentStepIndex)
  const isComplete = taskStatus === 'completed'
  const stepStatus = isComplete ? 'completed' : 'running'

  return (
    <div className="gen-page">
      {/* Background glow blobs */}
      <div className="gen-glow gen-glow--blue" />
      <div className="gen-glow gen-glow--purple" />

      {/* Back button */}
      <GenerationBackButton to="/home" label="← 返回学习首页" />

      {/* Center content */}
      <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {/* Progress dots */}
        <GenerationProgressDots steps={GENERATION_STEPS} currentStep={currentStepIndex} />

        {/* Step card */}
        <GenerationStepCard
          step={currentStep}
          stepProgress={stepProgress}
          status={stepStatus}
        />

        {/* Step counter below card */}
        <div style={{ marginTop: 16, fontSize: 13, color: '#9CA3AF', fontWeight: 500 }}>
          {isComplete
            ? '全部完成'
            : `步骤 ${currentStepIndex + 1} / ${GENERATION_STEPS.length}`
          }
        </div>

        {/* Completion hint */}
        {isComplete && (
          <div style={{ marginTop: 12, fontSize: 14, color: '#22C55E', fontWeight: 600 }}>
            🎉 学习资源已就绪，即将跳转到学习首页…
          </div>
        )}
      </div>

      {/* Agent log carousel */}
      <GenerationAgentLogCarousel activeStepIndex={currentStepIndex} />

      {/* View roles button */}
      <GenerationAgentPopover activeStepIndex={currentStepIndex} />

      {/* Footer hint */}
      <div className="gen-footer-hint">
        <div className="gen-footer-dot" />
        <span>AI 智能体工作中…</span>
      </div>
    </div>
  )
}
