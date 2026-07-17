import { useCallback, useRef } from 'react'
import {
  recordLearning,
  adaptLearningJourney,
  submitExerciseAnswer,
} from '../api/evaluate'

// 同一资源 5 分钟内不重复发送 view 事件
const VIEW_DEBOUNCE_MS = 5 * 60 * 1000

// 评估请求防抖：短时间多次 complete/answer 只触发一次评估
const EVALUATE_DEBOUNCE_MS = 2000

/**
 * 学习行为同步 Hook
 *
 * 提供 trackView / trackComplete / trackAnswer 三个行为追踪函数。
 *
 * 设计要点：
 * - view 操作仅写入记录，不触发 EvaluateAgent（避免每次浏览都调用）
 * - complete / answer 操作写入记录后触发评估流程
 * - 评估请求有 2 秒防抖，短时间多次提交只触发一次评估
 * - view 事件对同一资源 5 分钟内去重
 *
 * @param {Function} onEvaluationUpdate - 评估报告更新后的回调 (report) => void
 */
export function useLearningBehavior(studentId, onEvaluationUpdate) {
  const viewTimestamps = useRef({}) // resourceId → timestamp
  const evaluateTimer = useRef(null)
  const pendingRef = useRef(false)

  // ── 触发评估流程：POST /evaluate/start → GET /evaluate/report ──
  const triggerEvaluate = useCallback(async () => {
    // 已有等待中的评估 → 标记需要再次执行
    if (evaluateTimer.current) {
      pendingRef.current = true
      return
    }

    return new Promise((resolve) => {
      evaluateTimer.current = setTimeout(async () => {
        let latestReport = null
        do {
          pendingRef.current = false
          try {
            // 一次调用完成评估、路径自适应和薄弱点复习资源推送。
            if (!studentId) break
            const adaptation = await adaptLearningJourney({ student_id: studentId })
            const report = adaptation?.evaluation
            latestReport = report || latestReport
            if (onEvaluationUpdate && report) {
              // 确保 reviewPlan 兼容两种命名
              if (!report.reviewPlan?.length && report.review_plan?.length) {
                report.reviewPlan = report.review_plan
              }
              onEvaluationUpdate(report, adaptation)
            }
          } catch {
            // 评估失败不影响已经完成的学习行为。
          }
        } while (pendingRef.current)
        evaluateTimer.current = null
        resolve(latestReport)
      }, EVALUATE_DEBOUNCE_MS)
    })
  }, [studentId, onEvaluationUpdate])

  // ── 记录资源查看（防抖，静默失败）──
  const trackView = useCallback(async (resource) => {
    if (!resource?.id) return

    const now = Date.now()
    const lastView = viewTimestamps.current[resource.id] || 0
    if (now - lastView < VIEW_DEBOUNCE_MS) return
    viewTimestamps.current[resource.id] = now

    try {
      await recordLearning({
        student_id: studentId,
        action: 'view',
        resource_id: resource.id,
        topic: resource.topic || undefined,
      })
    } catch {
      // view 记录失败静默处理，不打断用户操作
    }
  }, [studentId])

  // ── 记录资源完成 → 触发评估 ──
  const trackComplete = useCallback(async (resource) => {
    if (!resource?.id) return

    await recordLearning({
      student_id: studentId,
      action: 'complete',
      resource_id: resource.id,
      topic: resource.topic || undefined,
    })

    // 触发评估刷新（内部有 2s 防抖）
    triggerEvaluate()
  }, [triggerEvaluate, studentId])

  // ── 记录练习作答（含分数）→ 触发评估 ──
  const trackAnswer = useCallback(async (resource, score) => {
    if (!resource?.id) return

    await recordLearning({
      student_id: studentId,
      action: 'answer',
      resource_id: resource.id,
      topic: resource.topic || undefined,
      score,
    })

    // 触发评估刷新（内部有 2s 防抖）
    triggerEvaluate()
  }, [triggerEvaluate, studentId])

  // ── 提交具体题目；后端根据正误自动维护错题本 ──
  const trackExerciseAnswer = useCallback(async (resource, quiz, userAnswer, isCorrect) => {
    if (!resource?.id || !quiz) return null

    const result = await submitExerciseAnswer({
      student_id: studentId,
      resource_id: resource.id,
      topic: resource.topic || undefined,
      question_id: String(quiz.id),
      question: quiz.question,
      options: quiz.options || [],
      user_answer: String(userAnswer),
      correct_answer: String(quiz.answer),
      explanation: quiz.explanation || undefined,
      is_correct: isCorrect,
    })
    triggerEvaluate()
    return result
  }, [triggerEvaluate, studentId])

  // ── 手动刷新评估（供外部直接调用）──
  const refreshEvaluation = useCallback(async () => {
    return triggerEvaluate()
  }, [triggerEvaluate])

  return { trackView, trackComplete, trackAnswer, trackExerciseAnswer, refreshEvaluation }
}
