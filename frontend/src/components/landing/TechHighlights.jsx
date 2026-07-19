import {
  DatabaseOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  UserOutlined,
  TeamOutlined,
  FileTextOutlined,
  SyncOutlined,
} from '@ant-design/icons'

const DATA_CARDS = [
  { icon: <UserOutlined />, label: '六维动态画像', value: '6 维度', color: '#6256e8' },
  { icon: <TeamOutlined />, label: '五智能体协同', value: '5 Agent', color: '#258cf4' },
  { icon: <FileTextOutlined />, label: '多类型学习资源', value: '讲义 / 题目 / 导图', color: '#2ac99a' },
  { icon: <SyncOutlined />, label: '评估驱动路径调整', value: '闭环反馈', color: '#eb2f96' },
]

const TECH_INNOVATIONS = [
  {
    icon: <DatabaseOutlined />,
    title: 'RAG 课程知识增强',
    desc: '基于 ChromaDB 和课程知识库进行检索增强生成，减少无依据内容输出，提高辅导准确性。',
    color: '#6256e8',
  },
  {
    icon: <ThunderboltOutlined />,
    title: '流式学习交互',
    desc: '基于 FastAPI SSE 实现画像分析、路径规划和辅导内容的逐步返回，提升交互体验。',
    color: '#258cf4',
  },
  {
    icon: <SafetyOutlined />,
    title: '安全与降级机制',
    desc: '内置内容过滤、错误重试、RAG 降级和结构化输出校验，保障系统稳定运行。',
    color: '#2ac99a',
  },
]

export default function TechHighlights() {
  return (
    <section className="lp-tech" id="tech">
      <div className="lp-section__header">
        <h2 className="lp-section__title">产品特色与技术创新</h2>
        <p className="lp-section__subtitle">
          以多智能体协作和 RAG 增强为核心，构建真正可落地的 AI 教育系统。
        </p>
      </div>

      {/* Data cards */}
      <div className="lp-tech__data-cards">
        {DATA_CARDS.map((card) => (
          <div key={card.label} className="lp-tech-data-card">
            <div className="lp-tech-data-card__icon" style={{ background: `${card.color}12`, color: card.color }}>
              {card.icon}
            </div>
            <div className="lp-tech-data-card__info">
              <span className="lp-tech-data-card__label">{card.label}</span>
              <span className="lp-tech-data-card__value" style={{ color: card.color }}>{card.value}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Tech innovations */}
      <div className="lp-tech__innovations">
        {TECH_INNOVATIONS.map((tech) => (
          <div key={tech.title} className="lp-tech-card">
            <div className="lp-tech-card__icon" style={{ background: `${tech.color}12`, color: tech.color }}>
              {tech.icon}
            </div>
            <h3 className="lp-tech-card__title">{tech.title}</h3>
            <p className="lp-tech-card__desc">{tech.desc}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
