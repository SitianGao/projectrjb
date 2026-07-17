import { regenerateEvaluation } from '../api/evaluate'

export async function requestRegenerateEvaluation(payload) {
  return regenerateEvaluation(payload)
}
