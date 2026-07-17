import { Button, Empty } from 'antd'

export default function EvaluationEmptyState({ onGenerate, loading }) {
  return (
    <div className="evaluation-empty">
      <Empty description="暂未生成学习评估">
        <p>完成学习任务或测评后，EvaluateAgent 将为你生成个性化诊断。</p>
        <Button type="primary" onClick={onGenerate} loading={loading}>生成首次评估</Button>
      </Empty>
    </div>
  )
}
