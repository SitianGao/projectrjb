import {
  UserOutlined,
  CompassOutlined,
  BookOutlined,
  RobotOutlined,
  BarChartOutlined,
} from '@ant-design/icons'

const FEATURES = [
  {
    icon: <UserOutlined />,
    agent: 'ProfileAgent',
    title: '对话式学习画像',
    desc: '通过自然语言构建六维学习画像，展示知识基础、学习目标、认知风格、薄弱点、学习历史和兴趣方向。',
    color: '#6256e8',
    preview: 'profile',
  },
  {
    icon: <CompassOutlined />,
    agent: 'PlannerAgent',
    title: '个性化路径规划',
    desc: '根据画像和课程目标生成分阶段学习路径，支持任务解锁和路径动态调整。',
    color: '#258cf4',
    preview: 'path',
  },
  {
    icon: <BookOutlined />,
    agent: 'ResourceAgent',
    title: '多类型资源生成',
    desc: '生成讲义、思维导图、练习题、代码案例和互动课堂资源，覆盖多种学习场景。',
    color: '#2ac99a',
    preview: 'resource',
  },
  {
    icon: <RobotOutlined />,
    agent: 'TutorAgent',
    title: '上下文智能辅导',
    desc: '根据当前课程、阶段和任务进行流式辅导，支持类比、公式、图解和案例等解释方式。',
    color: '#fa8c16',
    preview: 'tutor',
  },
  {
    icon: <BarChartOutlined />,
    agent: 'EvaluateAgent',
    title: '学习诊断与反馈',
    desc: '输出能力雷达图、薄弱知识点、学习建议和路径调整方案，驱动闭环优化。',
    color: '#eb2f96',
    preview: 'evaluate',
  },
]

// Simplified product preview illustrations (CSS-drawn)
function FeaturePreview({ type, color }) {
  const previewContent = {
    profile: (
      <div className="lp-feat-preview__chat">
        <div className="lp-feat-preview__bubble lp-feat-preview__bubble--ai" style={{ borderColor: color }}>
          <span style={{ color, fontWeight: 600 }}>AI</span> 你好！请介绍一下你的学习背景和目标？
        </div>
        <div className="lp-feat-preview__bubble lp-feat-preview__bubble--user">
          我是计算机专业大二学生，想学好机器学习...
        </div>
        <div className="lp-feat-preview__bubble lp-feat-preview__bubble--ai" style={{ borderColor: color }}>
          <span style={{ color, fontWeight: 600 }}>AI</span> 已为你构建六维学习画像 ✓
        </div>
        <div className="lp-feat-preview__mini-radar">
          <svg viewBox="0 0 60 60">
            <polygon points="30,5 52,18 52,42 30,55 8,42 8,18" fill="none" stroke={color} strokeWidth="1" opacity="0.3" />
            <polygon points="30,14 44,22 42,38 30,46 18,38 18,24" fill={color} opacity="0.15" stroke={color} strokeWidth="1" />
          </svg>
        </div>
      </div>
    ),
    path: (
      <div className="lp-feat-preview__path">
        {['基础概念', '核心算法', '模型训练', '项目实战'].map((step, i) => (
          <div key={i} className="lp-feat-preview__path-step">
            <div className="lp-feat-preview__path-dot" style={{ background: i < 2 ? color : '#e5e7eb' }} />
            <span style={{ color: i < 2 ? 'var(--lp-text-primary)' : 'var(--lp-text-muted)' }}>{step}</span>
            {i < 3 && <div className="lp-feat-preview__path-line" style={{ background: i < 1 ? color : '#e5e7eb' }} />}
          </div>
        ))}
        <div className="lp-feat-preview__path-badge" style={{ background: `${color}18`, color }}>
          已完成 2/4 阶段
        </div>
      </div>
    ),
    resource: (
      <div className="lp-feat-preview__resources">
        {[
          { icon: '📄', label: '讲义文档' },
          { icon: '🧠', label: '思维导图' },
          { icon: '✏️', label: '练习题' },
          { icon: '💻', label: '代码案例' },
        ].map((r, i) => (
          <div key={i} className="lp-feat-preview__resource-card">
            <span className="lp-feat-preview__resource-icon">{r.icon}</span>
            <span>{r.label}</span>
          </div>
        ))}
      </div>
    ),
    tutor: (
      <div className="lp-feat-preview__chat">
        <div className="lp-feat-preview__bubble lp-feat-preview__bubble--user">
          什么是梯度下降？能举个例子吗？
        </div>
        <div className="lp-feat-preview__bubble lp-feat-preview__bubble--ai" style={{ borderColor: color }}>
          <span style={{ color, fontWeight: 600 }}>AI</span> 想象你蒙着眼睛站在山上，想要下山到最低点...
          <div className="lp-feat-preview__analogy">
            <span>🏔️</span> → <span>📉</span> → <span>🎯</span>
          </div>
        </div>
      </div>
    ),
    evaluate: (
      <div className="lp-feat-preview__evaluate">
        <div className="lp-feat-preview__eval-score">
          <span className="lp-feat-preview__eval-number" style={{ color }}>78</span>
          <span className="lp-feat-preview__eval-label">综合评分</span>
        </div>
        <div className="lp-feat-preview__eval-bars">
          {[
            { label: '理论', value: 82, color: '#6256e8' },
            { label: '实践', value: 65, color: '#258cf4' },
            { label: '应用', value: 74, color: '#2ac99a' },
          ].map((b, i) => (
            <div key={i} className="lp-feat-preview__eval-bar">
              <span className="lp-feat-preview__eval-bar-label">{b.label}</span>
              <div className="lp-feat-preview__eval-bar-track">
                <div className="lp-feat-preview__eval-bar-fill" style={{ width: `${b.value}%`, background: b.color }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    ),
  }

  return <div className="lp-feat-preview">{previewContent[type]}</div>
}

export default function FeatureShowcase() {
  return (
    <section className="lp-features" id="features">
      <div className="lp-section__header">
        <h2 className="lp-section__title">从学习画像到动态评估，一套完整的个性化学习系统</h2>
        <p className="lp-section__subtitle">
          AI 不只是回答问题，而是持续理解学生、规划任务、生成资源并根据学习结果动态调整。
        </p>
      </div>

      <div className="lp-features__grid">
        {/* Row 1: 2 large cards */}
        <div className="lp-features__row lp-features__row--top">
          {FEATURES.slice(0, 2).map((f) => (
            <div key={f.title} className="lp-feature-card lp-feature-card--large">
              <div className="lp-feature-card__body">
                <div className="lp-feature-card__header">
                  <div className="lp-feature-card__icon" style={{ background: `${f.color}12`, color: f.color }}>
                    {f.icon}
                  </div>
                  <div>
                    <span className="lp-feature-card__agent" style={{ color: f.color }}>{f.agent}</span>
                    <h3 className="lp-feature-card__title">{f.title}</h3>
                  </div>
                </div>
                <p className="lp-feature-card__desc">{f.desc}</p>
              </div>
              <FeaturePreview type={f.preview} color={f.color} />
            </div>
          ))}
        </div>

        {/* Row 2: 3 normal cards */}
        <div className="lp-features__row lp-features__row--bottom">
          {FEATURES.slice(2).map((f) => (
            <div key={f.title} className="lp-feature-card">
              <div className="lp-feature-card__header">
                <div className="lp-feature-card__icon" style={{ background: `${f.color}12`, color: f.color }}>
                  {f.icon}
                </div>
                <div>
                  <span className="lp-feature-card__agent" style={{ color: f.color }}>{f.agent}</span>
                  <h3 className="lp-feature-card__title">{f.title}</h3>
                </div>
              </div>
              <p className="lp-feature-card__desc">{f.desc}</p>
              <FeaturePreview type={f.preview} color={f.color} />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
