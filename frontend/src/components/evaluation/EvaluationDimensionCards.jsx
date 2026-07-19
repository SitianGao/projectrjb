import EvaluationDimensionCard from './EvaluationDimensionCard'

export default function EvaluationDimensionCards({ dimensions = [] }) {
  const items = Array.isArray(dimensions)
    ? dimensions
    : Object.entries(dimensions || {}).map(([key, value]) => ({
        name: key,
        label: {
          knowledge_mastery: '知识掌握度',
          test_accuracy: '测评正确率',
          task_completion: '任务完成度',
          learning_consistency: '学习连续性',
          error_correction: '纠错能力',
          practice_ability: '实践能力',
        }[key] || key,
        score: value,
        comment: '基于当前课程范围内的有效学习数据计算。',
      }))
  return (
    <div className="dimension-grid">
      {items.map((item) => <EvaluationDimensionCard key={item.name || item.label} item={item} />)}
    </div>
  )
}
