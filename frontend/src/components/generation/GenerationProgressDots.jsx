import { CheckCircleFilled } from '@ant-design/icons'

export default function GenerationProgressDots({ steps, currentStep }) {
  return (
    <div className="gen-dots">
      {steps.map((_step, i) => {
        const isActive = i === currentStep
        const isDone = i < currentStep
        return (
          <div
            key={i}
            className={
              'gen-dot' +
              (isActive ? ' gen-dot--active' : '') +
              (isDone ? ' gen-dot--done' : '') +
              (!isActive && !isDone ? ' gen-dot--pending' : '')
            }
          />
        )
      })}
    </div>
  )
}
