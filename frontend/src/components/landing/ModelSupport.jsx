const MODELS = [
  { name: '讯飞星火', tag: '已接入' },
  { name: 'DeepSeek', tag: '已接入' },
  { name: 'OpenAI Compatible', tag: '支持接入' },
]

const TECH_STACK = [
  { name: 'FastAPI', desc: '后端框架' },
  { name: 'React', desc: '前端框架' },
  { name: 'ChromaDB', desc: '向量数据库' },
  { name: 'LangGraph', desc: '智能体编排' },
]

export default function ModelSupport() {
  return (
    <section className="lp-models" id="demo">
      <div className="lp-section__header">
        <h2 className="lp-section__title">支持主流大模型灵活切换</h2>
        <p className="lp-section__subtitle">
          架构设计支持多模型接入，可根据需求灵活切换底层大语言模型。
        </p>
      </div>

      <div className="lp-models__grid">
        {MODELS.map((model) => (
          <div key={model.name} className="lp-model-badge">
            <span className="lp-model-badge__name">{model.name}</span>
            <span className="lp-model-badge__tag">{model.tag}</span>
          </div>
        ))}
      </div>

      <div className="lp-models__stack">
        {TECH_STACK.map((tech) => (
          <div key={tech.name} className="lp-stack-item">
            <span className="lp-stack-item__name">{tech.name}</span>
            <span className="lp-stack-item__desc">{tech.desc}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
