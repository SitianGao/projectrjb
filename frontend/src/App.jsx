import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import { Layout, Menu, Typography } from 'antd'
import {
  HomeOutlined,
  UserOutlined,
  RiseOutlined,
  FileTextOutlined,
  BookOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import LoadingSkeleton from './components/LoadingSkeleton'
import './App.css'

// 页面组件懒加载
const HomePage = lazy(() => import('./pages/HomePage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const LearningPathPage = lazy(() => import('./pages/LearningPathPage'))
const ResourcePage = lazy(() => import('./pages/ResourcePage'))
const TutorPage = lazy(() => import('./pages/TutorPage'))
const EvaluatePage = lazy(() => import('./pages/EvaluatePage'))

const { Header, Content, Sider } = Layout
const { Text } = Typography

const menuItems = [
  { key: '/', icon: <HomeOutlined />, label: '仪表盘' },
  { key: '/profile', icon: <UserOutlined />, label: '学生画像' },
  { key: '/learning-path', icon: <RiseOutlined />, label: '学习路径' },
  { key: '/resources', icon: <FileTextOutlined />, label: '学习资源' },
  { key: '/tutor', icon: <BookOutlined />, label: '智能辅导' },
  { key: '/evaluate', icon: <TrophyOutlined />, label: '学习评估' },
]

function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()

  // 计算当前选中的菜单项
  const selectedKey = menuItems
    .filter((item) => item.key !== '/')
    .find((item) => location.pathname.startsWith(item.key))?.key || '/'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边导航 */}
      <Sider
        breakpoint="lg"
        collapsedWidth="64"
        width={220}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 10,
        }}
      >
        <div className="logo">
          <Text strong style={{ color: '#fff', fontSize: 18 }}>
            📚 智能学习平台
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      {/* 主内容区 */}
      <Layout style={{ marginLeft: 220 }}>
        {/* 顶部栏 */}
        <Header className="site-header">
          <Text strong style={{ fontSize: 16 }}>
            {menuItems.find((item) => {
              if (item.key === '/') return location.pathname === '/'
              return location.pathname.startsWith(item.key)
            })?.label || '智能学习平台'}
          </Text>
        </Header>

        {/* 页面内容 */}
        <Content className="site-content">
          <Suspense fallback={<LoadingSkeleton type="detail" />}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/learning-path" element={<LearningPathPage />} />
              <Route path="/resources" element={<ResourcePage />} />
              <Route path="/tutor" element={<TutorPage />} />
              <Route path="/evaluate" element={<EvaluatePage />} />
            </Routes>
          </Suspense>
        </Content>
      </Layout>
    </Layout>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}
