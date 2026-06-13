import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, useLocation, useNavigate, Navigate } from 'react-router-dom'
import { Typography, Dropdown, Avatar } from 'antd'
import {
  HomeOutlined,
  ArrowLeftOutlined,
  UserOutlined,
  LogoutOutlined,
  KeyOutlined,
  EditOutlined,
  SunOutlined,
  MoonOutlined,
  ReadOutlined,
} from '@ant-design/icons'
import LoadingSkeleton from './components/LoadingSkeleton'
import NotificationCenter from './components/NotificationCenter'
import { useAuth } from './contexts/AuthContext'
import { ThemeProvider, useTheme, THEMES } from './contexts/ThemeContext'
import './App.css'

// 页面组件懒加载
const LandingPage = lazy(() => import('./pages/LandingPage'))
const HomePage = lazy(() => import('./pages/HomePage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const TutorPage = lazy(() => import('./pages/TutorPage'))
const DocsPage = lazy(() => import('./pages/DocsPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'))

const { Text } = Typography

// 需要登录才能访问的布局
function AuthLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { mode, setMode, resolved } = useTheme()

  // 用户下拉菜单项
  const userMenuItems = [
    {
      key: 'user-info',
      label: (
        <div style={{ padding: '4px 0', cursor: 'default' }}>
          <Text strong>{user?.name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>{user?.email}</Text>
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'edit-profile',
      icon: <EditOutlined />,
      label: '修改信息',
    },
    {
      key: 'change-password',
      icon: <KeyOutlined />,
      label: '修改密码',
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: <span style={{ color: '#ff4d4f' }}>退出登录</span>,
      danger: true,
      onClick: () => {
        logout()
        navigate('/login', { replace: true })
      },
    },
  ]

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-page)' }}>
      {/* 顶部导航栏 */}
      <div className="top-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <Text strong style={{ color: 'var(--text-primary)', fontSize: 18, cursor: 'pointer' }} onClick={() => navigate('/')}>
            🤖 智能学习平台
          </Text>
          <span
            onClick={() => navigate('/landing')}
            style={{
              fontSize: 14,
              color: location.pathname === '/landing' ? '#8b5cf6' : 'var(--text-secondary)',
              fontWeight: location.pathname === '/landing' ? 600 : 400,
              cursor: 'pointer',
              transition: 'color 0.2s',
              userSelect: 'none',
            }}
            onMouseEnter={(e) => { if (location.pathname !== '/landing') e.target.style.color = '#8b5cf6' }}
            onMouseLeave={(e) => { if (location.pathname !== '/landing') e.target.style.color = 'var(--text-secondary)' }}
          >
            主页
          </span>
          <span
            onClick={() => navigate('/docs')}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              fontSize: 14,
              color: location.pathname === '/docs' ? '#8b5cf6' : 'var(--text-secondary)',
              fontWeight: location.pathname === '/docs' ? 600 : 400,
              cursor: 'pointer',
              transition: 'color 0.2s',
              userSelect: 'none',
            }}
            onMouseEnter={(e) => { if (location.pathname !== '/docs') e.target.style.color = '#8b5cf6' }}
            onMouseLeave={(e) => { if (location.pathname !== '/docs') e.target.style.color = 'var(--text-secondary)' }}
          >
            <ReadOutlined /> 文档
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* 通知 */}
          <NotificationCenter />

          {/* 主题切换 */}
          <Dropdown menu={{
            items: Object.values(THEMES).map((t) => ({
              key: t.key,
              icon: t.icon === 'sun' ? <SunOutlined /> : t.icon === 'moon' ? <MoonOutlined /> : <SunOutlined style={{ opacity: 0.5 }} />,
              label: t.label,
              onClick: () => setMode(t.key),
            })),
            selectedKeys: [mode],
          }} placement="bottomRight" trigger={['click']}>
            <div className="top-home-btn" title="主题切换">
              {resolved === 'dark' ? <MoonOutlined /> : <SunOutlined />}
            </div>
          </Dropdown>

          {/* 个人中心 / 画像 */}
          <div className="top-home-btn" onClick={() => navigate(location.pathname === '/home' ? '/' : '/home')}
            title={location.pathname === '/home' ? '平台主页' : '个人中心'}>
            {location.pathname === '/home' ? <ArrowLeftOutlined /> : <HomeOutlined />}
          </div>

          {/* 用户头像下拉 */}
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" trigger={['click']}>
            <div className="top-user-btn">
              <Avatar size={30} icon={<UserOutlined />} style={{ backgroundColor: '#1677ff' }} />
              <span className="top-user-name">{user?.name}</span>
            </div>
          </Dropdown>
        </div>
      </div>

      {/* 内容区（全宽） */}
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
        <Suspense fallback={<LoadingSkeleton type="detail" />}>
          <Routes>
            <Route path="/" element={<ProfilePage />} />
            <Route path="/home" element={<HomePage />} />
            <Route path="/landing" element={<LandingPage />} />
            <Route path="/tutor" element={<TutorPage />} />
            <Route path="/docs" element={<DocsPage />} />
          </Routes>
        </Suspense>
      </div>
    </div>
  )
}

// 路由守卫：未登录重定向到登录页
function RequireAuth({ children }) {
  const { isLoggedIn } = useAuth()
  if (!isLoggedIn) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
        {/* 登录/注册/忘记密码 — 独立页面，不需要布局 */}
        <Route path="/forgot-password" element={
          <Suspense fallback={<LoadingSkeleton type="detail" />}>
            <ForgotPasswordPage />
          </Suspense>
        } />
        <Route path="/login" element={
          <Suspense fallback={<LoadingSkeleton type="detail" />}>
            <LoginPage />
          </Suspense>
        } />
        <Route path="/register" element={
          <Suspense fallback={<LoadingSkeleton type="detail" />}>
            <RegisterPage />
          </Suspense>
        } />

        {/* 需要登录的页面 */}
        <Route path="/*" element={
          <RequireAuth>
            <AuthLayout />
          </RequireAuth>
        } />
      </Routes>
    </BrowserRouter>
    </ThemeProvider>
  )
}
