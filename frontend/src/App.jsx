import { lazy, Suspense, useState } from 'react'
import { BrowserRouter, Routes, Route, useLocation, useNavigate, Navigate } from 'react-router-dom'
import { Layout, Menu, Typography, Dropdown, Avatar } from 'antd'
import {
  HomeOutlined,
  UserOutlined,
  MessageOutlined,
  RiseOutlined,
  FileTextOutlined,
  BookOutlined,
  TrophyOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  LogoutOutlined,
  KeyOutlined,
  EditOutlined,
} from '@ant-design/icons'
import LoadingSkeleton from './components/LoadingSkeleton'
import { useAuth } from './contexts/AuthContext'
import './App.css'

// 页面组件懒加载
const HomePage = lazy(() => import('./pages/HomePage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const LearningPathPage = lazy(() => import('./pages/LearningPathPage'))
const ResourcePage = lazy(() => import('./pages/ResourcePage'))
const TutorPage = lazy(() => import('./pages/TutorPage'))
const EvaluatePage = lazy(() => import('./pages/EvaluatePage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))

const { Content, Sider } = Layout
const { Text } = Typography

const menuItems = [
  { key: '/', icon: <MessageOutlined />, label: '对话' },
  { key: '/home', icon: <HomeOutlined />, label: '个人中心' },
  { key: '/learning-path', icon: <RiseOutlined />, label: '学习路径' },
  { key: '/resources', icon: <FileTextOutlined />, label: '学习资源' },
  { key: '/tutor', icon: <BookOutlined />, label: '智能辅导' },
  { key: '/evaluate', icon: <TrophyOutlined />, label: '学习评估' },
]

// 需要登录才能访问的布局
function AuthLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [collapsed, setCollapsed] = useState(false)
  const [pinned, setPinned] = useState(false)

  // 计算当前选中的菜单项
  const selectedKey = (() => {
    if (location.pathname === '/') return '/'
    return menuItems
      .filter((item) => item.key !== '/')
      .find((item) => location.pathname.startsWith(item.key))?.key || ''
  })()

  const handleMouseEnter = () => {
    if (!pinned) setCollapsed(false)
  }
  const handleMouseLeave = () => {
    if (!pinned) setCollapsed(true)
  }
  const handleToggle = () => {
    if (pinned) {
      setPinned(false)
      setCollapsed(true)
    } else {
      setPinned(true)
      setCollapsed(false)
    }
  }

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
      onClick: () => {
        // TODO: 打开修改信息弹窗
      },
    },
    {
      key: 'change-password',
      icon: <KeyOutlined />,
      label: '修改密码',
      onClick: () => {
        // TODO: 打开修改密码弹窗
      },
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
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', background: '#f5f5f5' }}>
      {/* 上菜单栏 */}
      <div className="top-bar">
        <Text strong style={{ color: '#fff', fontSize: 18 }}>
          📚 智能学习平台
        </Text>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* 个人中心 */}
          <div
            className={`top-home-btn ${location.pathname === '/home' ? 'active' : ''}`}
            onClick={() => navigate('/home')}
            title="个人中心"
          >
            <HomeOutlined />
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

      {/* 下方：左侧菜单 + 右侧内容 */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <Sider
          breakpoint="lg"
          collapsedWidth="64"
          width={150}
          collapsed={collapsed}
          onCollapse={(value) => setCollapsed(value)}
          trigger={null}
          style={{ overflowY: 'auto', overflowX: 'hidden' }}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <div className={`sider-toggle ${pinned ? 'pinned' : ''}`} onClick={handleToggle} title={pinned ? '取消固定' : '固定侧边栏'}>
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            {pinned && !collapsed && <span className="pin-dot" />}
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={selectedKey ? [selectedKey] : []}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            className="compact-menu"
          />
        </Sider>

        <Content className="site-content">
          <Suspense fallback={<LoadingSkeleton type="detail" />}>
            <Routes>
              <Route path="/" element={<ProfilePage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/home" element={<HomePage />} />
              <Route path="/learning-path" element={<LearningPathPage />} />
              <Route path="/resources" element={<ResourcePage />} />
              <Route path="/tutor" element={<TutorPage />} />
              <Route path="/evaluate" element={<EvaluatePage />} />
            </Routes>
          </Suspense>
        </Content>
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
    <BrowserRouter>
      <Routes>
        {/* 登录/注册 — 独立页面，不需要布局 */}
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
  )
}
