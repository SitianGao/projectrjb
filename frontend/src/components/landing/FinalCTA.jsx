import { Button, Space } from 'antd'
import { RocketOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

export default function FinalCTA() {
  const navigate = useNavigate()

  return (
    <section className="lp-cta">
      <div className="lp-cta__inner">
        <h2 className="lp-cta__title">开启属于你的个性化学习路径</h2>
        <p className="lp-cta__desc">
          从一次自然语言对话开始，让 EduAgent 理解你的目标、基础与薄弱点，并生成完整的学习计划。
        </p>
        <Space size={16}>
          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            className="lp-cta__btn-primary"
            onClick={() => navigate('/login')}
          >
            立即开始学习
          </Button>
          <Button
            size="large"
            icon={<PlayCircleOutlined />}
            className="lp-cta__btn-secondary"
            onClick={() => {
              const el = document.querySelector('#demo')
              if (el) el.scrollIntoView({ behavior: 'smooth' })
            }}
          >
            查看产品演示
          </Button>
        </Space>
      </div>
    </section>
  )
}
