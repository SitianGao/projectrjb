import { RobotOutlined } from '@ant-design/icons'

export default function LandingFooter() {
  return (
    <footer className="lp-footer">
      <div className="lp-footer__inner">
        <div className="lp-footer__brand">
          <RobotOutlined className="lp-footer__icon" />
          <span className="lp-footer__name">智学相伴</span>
        </div>
        <div className="lp-footer__info">
          <span>第十五届中国软件杯 A3 赛题作品</span>
        </div>
        <div className="lp-footer__tech">
          技术栈：React + FastAPI + LangGraph + ChromaDB
        </div>
        <div className="lp-footer__note">
          本项目为参赛作品，页面中展示的功能基于实际开发成果，未使用虚构数据。
        </div>
      </div>
    </footer>
  )
}
