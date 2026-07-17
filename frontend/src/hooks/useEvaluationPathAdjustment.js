import { useState } from 'react'
import { message } from 'antd'
import {
  applyEvaluationPathAdjustment,
  previewEvaluationPathAdjustment,
} from '../services/pathAdjustmentService'

export default function useEvaluationPathAdjustment() {
  const [loading, setLoading] = useState(false)

  async function preview(evaluationId) {
    setLoading(true)
    try {
      return await previewEvaluationPathAdjustment(evaluationId)
    } finally {
      setLoading(false)
    }
  }

  async function apply(evaluationId) {
    setLoading(true)
    try {
      const result = await applyEvaluationPathAdjustment(evaluationId)
      message.success('已确认路径调整建议')
      return result
    } finally {
      setLoading(false)
    }
  }

  return { preview, apply, loading }
}
