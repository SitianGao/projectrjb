import { useState, useEffect } from 'react'
import { Button } from 'antd'
import { RobotOutlined, MenuOutlined, CloseOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const NAV_ITEMS = [
  { label: '产品能力', href: '#features' },
  { label: '智能体', href: '#agents' },
  { label: '学习闭环', href: '#loop' },
  { label: '技术创新', href: '#tech' },
  { label: '产品演示', href: '#demo' },
]

export default function LandingNavbar() {
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const handleNav = (href) => {
    setMobileOpen(false)
    const el = document.querySelector(href)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <nav className={`lp-navbar${scrolled ? ' lp-navbar--scrolled' : ''}`}>
      <div className="lp-navbar__inner">
        <div className="lp-navbar__brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <RobotOutlined className="lp-navbar__logo-icon" />
          <span className="lp-navbar__logo-text">EduAgent</span>
          <span className="lp-navbar__logo-sub">智能学习平台</span>
        </div>

        <div className="lp-navbar__links">
          {NAV_ITEMS.map((item) => (
            <a key={item.href} className="lp-navbar__link" onClick={() => handleNav(item.href)}>
              {item.label}
            </a>
          ))}
        </div>

        <div className="lp-navbar__actions">
          <Button type="text" className="lp-navbar__login-btn" onClick={() => navigate('/login')}>
            登录
          </Button>
          <Button type="primary" className="lp-navbar__cta-btn" onClick={() => navigate('/login')}>
            开始学习
          </Button>
        </div>

        <button className="lp-navbar__hamburger" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <CloseOutlined /> : <MenuOutlined />}
        </button>
      </div>

      {mobileOpen && (
        <div className="lp-navbar__mobile">
          {NAV_ITEMS.map((item) => (
            <a key={item.href} className="lp-navbar__mobile-link" onClick={() => handleNav(item.href)}>
              {item.label}
            </a>
          ))}
          <div className="lp-navbar__mobile-actions">
            <Button block onClick={() => { setMobileOpen(false); navigate('/login') }}>登录</Button>
            <Button type="primary" block onClick={() => { setMobileOpen(false); navigate('/login') }}>开始学习</Button>
          </div>
        </div>
      )}
    </nav>
  )
}
