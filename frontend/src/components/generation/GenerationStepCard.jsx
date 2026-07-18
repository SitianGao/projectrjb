import { CheckCircleFilled, LoadingOutlined } from '@ant-design/icons'

export default function GenerationStepCard({ step, stepProgress, status }) {
  const isRunning = status === 'running'
  const isDone = status === 'completed'

  return (
    <div className={'gen-step-card' + (isDone ? ' gen-step-card--done' : '')}>
      {/* Icon */}
      <div
        className={
          'gen-step-icon-wrap' +
          (isRunning ? ' gen-step-icon-wrap--running' : '') +
          (isDone ? ' gen-step-icon-wrap--done' : '') +
          (!isRunning && !isDone ? ' gen-step-icon-wrap--waiting' : '')
        }
      >
        {isDone ? (
          <CheckCircleFilled className="gen-step-icon--done" />
        ) : isRunning ? (
          <span className="gen-step-icon">{step.icon}</span>
        ) : (
          <span className="gen-step-icon gen-step-icon--waiting">{step.icon}</span>
        )}
        {/* Running ring */}
        {isRunning && (
          <div
            style={{
              position: 'absolute',
              inset: -4,
              borderRadius: '50%',
              border: '2px solid transparent',
              borderTopColor: 'rgba(108,92,231,0.3)',
              animation: 'gen-pulse 1.2s linear infinite',
            }}
          />
        )}
      </div>

      {/* Title */}
      <h2 className="gen-step-title">
        {isDone ? '✅ ' : isRunning ? '' : ''}
        {step.title}
      </h2>

      {/* Subtitle */}
      <p className="gen-step-subtitle">{step.subtitle}</p>

      {/* Progress bar (only when running) */}
      {isRunning && (
        <div className="gen-step-progress-wrap">
          <div
            className="gen-step-progress-fill"
            style={{ width: `${Math.max(stepProgress, 5)}%` }}
          />
        </div>
      )}

      {/* Completion summary */}
      {isDone && (
        <div style={{ color: '#9CA3AF', fontSize: 13, marginTop: 8 }}>
          全部 5 个步骤已完成
        </div>
      )}
    </div>
  )
}
