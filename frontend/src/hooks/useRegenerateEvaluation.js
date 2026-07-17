import { useState } from 'react'
import { message } from 'antd'
import { normalizeReport } from '../services/evaluationService'
import { requestRegenerateEvaluation } from '../services/evaluateAgentService'

export default function useRegenerateEvaluation() {
  const [regenerating, setRegenerating] = useState(false)

  async function regenerate(payload) {
    setRegenerating(true)
    try {
      const data = await requestRegenerateEvaluation(payload)
      const report = normalizeReport(data)
      if (data?.can_generate === false || report?.canGenerate === false) {
        message.info('暂无新的学习数据，建议完成新的学习任务或测评后再重新评估。')
      } else {
        message.success('评估报告已更新')
      }
      return report
    } catch (err) {
      message.error(err.message || '重新评估失败')
      throw err
    } finally {
      setRegenerating(false)
    }
  }

  return { regenerate, regenerating }
}
