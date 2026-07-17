import { applyPathAdjustment, previewPathAdjustment } from '../api/evaluate'

export async function previewEvaluationPathAdjustment(evaluationId) {
  return previewPathAdjustment(evaluationId)
}

export async function applyEvaluationPathAdjustment(evaluationId) {
  return applyPathAdjustment(evaluationId)
}
