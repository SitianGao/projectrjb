import {
  UserOutlined,
  CompassOutlined,
  ReadOutlined,
  BarChartOutlined,
} from '@ant-design/icons'

const STEPS = [
  {
    icon: <UserOutlined />,
    title: '构建画像',
    desc: '通过对话式交互，AI 自动构建包含知识基础、学习目标、认知风格等六维度的学生画像。',
    color: '#6256e8',
    screenshot: '/screenshots/frontend-profile-final.png',
  },
  {
    icon: <CompassOutlined />,
    title: '生成路径',
    desc: 'PlannerAgent 根据画像和课程目标，生成分阶段、可解锁的个性化学习路径。',
    color: '#258cf4',
    screenshot: '/screenshots/frontend-learning-path.png',
  },
  {
    icon: <ReadOutlined />,
    title: '执行任务',
    desc: '学生按照路径学习，ResourceAgent 生成讲义、练习题等资源，TutorAgent 提供实时辅导。',
    color: '#2ac99a',
    screenshot: '/screenshots/frontend-home.png',
  },
  {
    icon: <BarChartOutlined />,
    title: '学习评估',
    desc: 'EvaluateAgent 对学习成果进行多维度评估，输出能力雷达图和薄弱知识点诊断。',
    color: '#fa8c16',
    screenshot: '/screenshots/report-full.png',
  },
]

function StepCard({ step, index, total }) {
  return (
    <div className="lp-loop-step">
      <div className="lp-loop-step__number" style={{ background: step.color, color: '#fff' }}>
        {index + 1}
      </div>
      <div className="lp-loop-step__content">
        <div className="lp-loop-step__header">
          <span className="lp-loop-step__icon" style={{ color: step.color }}>{step.icon}</span>
          <h3 className="lp-loop-step__title">{step.title}</h3>
        </div>
        <p className="lp-loop-step__desc">{step.desc}</p>
        {step.screenshot && (
          <div className="lp-loop-step__preview">
            <div className="lp-loop-step__preview-bar">
              <span className="lp-preview-dot lp-preview-dot--red" />
              <span className="lp-preview-dot lp-preview-dot--yellow" />
              <span className="lp-preview-dot lp-preview-dot--green" />
            </div>
            <img src={step.screenshot} alt={step.title} className="lp-loop-step__img" loading="lazy" />
          </div>
        )}
        {!step.screenshot && (
          <div className="lp-loop-step__preview lp-loop-step__preview--icon">
            <SyncOutlined style={{ fontSize: 48, color: step.color, opacity: 0.4 }} />
          </div>
        )}
      </div>
      {index < total - 1 && <div className="lp-loop-step__connector" />}
    </div>
  )
}

export default function LearningLoop() {
  return (
    <section className="lp-loop" id="loop">
      <div className="lp-section__header">
        <h2 className="lp-section__title">一条能够持续自我调整的学习闭环</h2>
        <p className="lp-section__subtitle">
          从画像构建到动态调整，每一步都基于真实学习数据驱动，确保学习路径始终适合学生当前状态。
        </p>
      </div>

      <div className="lp-loop__steps">
        {STEPS.map((step, i) => (
          <StepCard key={step.title} step={step} index={i} total={STEPS.length} />
        ))}
      </div>
    </section>
  )
}
