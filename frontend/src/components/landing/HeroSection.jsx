import { Button, Space, Tag } from 'antd'
import { RocketOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import ProductPreview from './ProductPreview'

const CAPABILITY_TAGS = [
  '五大智能体协同',
  '六维动态学习画像',
  'RAG 知识增强',
  '实时学习诊断',
]

export default function HeroSection() {
  const navigate = useNavigate()

  return (
    <section className="lp-hero">
      <div className="lp-hero__bg">
        <div className="lp-hero__glow lp-hero__glow--1" />
        <div className="lp-hero__glow lp-hero__glow--2" />
      </div>

      <div className="lp-hero__inner">
        <div className="lp-hero__content">
          <Tag className="lp-hero__tag" color="purple">
            第十五届中国软件杯 A3 赛题作品
          </Tag>

          <h1 className="lp-hero__title">
            让 AI 为每位学生
            <br />
            规划真正
            <span className="lp-hero__gradient">个性化的学习路径</span>
          </h1>

          <p className="lp-hero__subtitle">
            基于大模型、课程知识库与多智能体协作，围绕学生画像、路径规划、资源生成、智能辅导和学习评估，构建可持续调整的个性化学习闭环。
          </p>

          <Space size={16} className="lp-hero__buttons">
            <Button
              type="primary"
              size="large"
              icon={<RocketOutlined />}
              className="lp-hero__cta-primary"
              onClick={() => navigate('/login')}
            >
              开始学习
            </Button>
            <Button
              size="large"
              icon={<PlayCircleOutlined />}
              className="lp-hero__cta-secondary"
              onClick={() => {
                const el = document.querySelector('#demo')
                if (el) el.scrollIntoView({ behavior: 'smooth' })
              }}
            >
              查看产品演示
            </Button>
          </Space>

          <div className="lp-hero__tags">
            {CAPABILITY_TAGS.map((tag) => (
              <span key={tag} className="lp-hero__cap-tag">
                <span className="lp-hero__cap-dot" />
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="lp-hero__preview">
          <ProductPreview />
        </div>
      </div>
    </section>
  )
}
