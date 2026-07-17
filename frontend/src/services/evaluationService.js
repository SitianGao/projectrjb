import {
  getCourseEvaluation,
  getEvaluationReport,
  getEvaluationReports,
} from '../api/evaluate'

export const SCOPE_OPTIONS = [
  { label: '最近 7 天', value: 'last_7_days' },
  { label: '最近 30 天', value: 'last_30_days' },
  { label: '当前阶段', value: 'current_stage' },
  { label: '当前课程全部', value: 'course_all' },
]

export function clampScore(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.max(0, Math.min(100, Math.round(number)))
}

export function normalizeReport(raw) {
  if (!raw) return null
  const structured = raw.structured || {}
  const overall = raw.overall || structured.overall || {}
  const dataSummary = raw.data_summary || raw.dataSummary || structured.data_summary || {}
  const scope = raw.scope || structured.scope || {}
  return {
    ...raw,
    evaluationId: raw.evaluation_id || raw.report_id,
    courseId: raw.course_id || structured.course_id,
    courseName: raw.course_name || structured.course_name || '当前课程',
    stageId: raw.stage_id || structured.stage_id,
    stageTitle: raw.stage_title || structured.stage_title || '',
    scope,
    dataSummary,
    overall: {
      score: clampScore(overall.score ?? raw.overall_score ?? raw.overallScore),
      previous_score: overall.previous_score,
      score_delta: Number(overall.score_delta || 0),
      period_average: clampScore(overall.period_average),
      confidence: Number(overall.confidence ?? 0),
      level: overall.level || '基础掌握',
      short_term_trend: overall.short_term_trend || raw.recent_trend || 'insufficient_data',
      long_term_trend: overall.long_term_trend || 'insufficient_data',
    },
    dimensionCards: raw.dimension_cards || structured.dimension_cards || raw.dimensions || [],
    strengths: raw.strengths || structured.strengths || [],
    weaknesses: raw.weaknesses || structured.weaknesses || [],
    summary: raw.summary || structured.summary || raw.suggestions?.[0] || '',
    pathAdjustments: raw.path_adjustments || raw.pathAdjustments || structured.path_adjustments || [],
    courseProgress: raw.course_progress || raw.courseProgress || structured.course_progress || {},
    history: raw.history || [],
    generatedAt: structured.generated_at || raw.created_at,
    canGenerate: raw.can_generate !== false,
    reason: raw.reason,
  }
}

export async function fetchEvaluationReport({ studentId, courseId, scope, stageId, reportId }) {
  if (reportId) return normalizeReport(await getEvaluationReport(reportId))
  return normalizeReport(await getCourseEvaluation({
    student_id: studentId,
    course_id: courseId,
    scope_type: scope,
    stage_id: stageId,
  }))
}

export async function fetchEvaluationHistory({ studentId, courseId }) {
  const rows = await getEvaluationReports({ student_id: studentId, course_id: courseId })
  return Array.isArray(rows) ? rows.map(normalizeReport) : []
}

export function getTrendLabel(trend) {
  return {
    improving: '持续上升',
    recovering: '短期回升',
    stable: '基本稳定',
    declining: '整体下降',
    insufficient_data: '数据不足',
    up: '短期回升',
    flat: '基本稳定',
    down: '整体下降',
  }[trend] || '数据不足'
}

export function confidenceLabel(value) {
  const pct = Math.round(Number(value || 0) * 100)
  if (pct >= 80) return `${pct}% · 较高`
  if (pct >= 55) return `${pct}% · 中等`
  return `${pct}% · 较低`
}
