import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route, useLocation, useNavigate, Navigate, useParams } from 'react-router-dom'
import { Typography, Dropdown, Avatar } from 'antd'
import {
  UserOutlined,
  LogoutOutlined,
  KeyOutlined,
  EditOutlined,
  SunOutlined,
  MoonOutlined,
  DesktopOutlined,
  ReadOutlined,
  BookOutlined,
  BranchesOutlined,
  CheckCircleOutlined,
  FileTextOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import LoadingSkeleton from './components/LoadingSkeleton'
import NotificationCenter from './components/NotificationCenter'
import PageErrorBoundary from './components/PageErrorBoundary'
import FloatingTutor from './components/FloatingTutor'
import { useAuth } from './contexts/AuthContext'
import { useTheme, THEMES } from './contexts/ThemeContext'
import { TutorProvider } from './contexts/TutorContext.jsx'
import './App.css'

// 页面组件懒加载
const LandingPage = lazy(() => import('./pages/LandingPage'))
const HomePage = lazy(() => import('./pages/HomePage'))
const StudyHomePage = lazy(() => import('./pages/StudyHomePage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const ProfileSetupPage = lazy(() => import('./pages/ProfileSetupPage'))
const AIWorkspacePage = lazy(() => import('./pages/AIWorkspacePage'))
const CourseEntryPage = lazy(() => import('./pages/CourseEntryPage'))
const DocsPage = lazy(() => import('./pages/DocsPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'))
const ResourcePage = lazy(() => import('./pages/ResourcePage'))
const ResourceDetailPage = lazy(() => import('./pages/ResourceDetailPage'))
const LearningPathPage = lazy(() => import('./pages/LearningPathPage'))
const LearningJourneyPage = lazy(() => import('./pages/LearningJourneyPage'))
const StageResourcePage = lazy(() => import('./pages/StageResourcePage'))
const WrongBookPage = lazy(() => import('./pages/WrongBookPage'))
const InteractiveClassroomPage = lazy(() => import('./pages/InteractiveClassroomPage'))
const EditProfilePage = lazy(() => import('./pages/EditProfilePage'))
const ChangePasswordPage = lazy(() => import('./pages/ChangePasswordPage'))
const CodePracticePage = lazy(() => import('./pages/CodePracticePage'))
const CodeExperimentPage = lazy(() => import('./pages/CodeExperimentPage'))
const EvaluatePage = lazy(() => import('./pages/EvaluationReportPage'))
const LearningAssessmentPage = lazy(() => import('./pages/LearningAssessmentPage'))

const { Text } = Typography

// 需要登录才能访问的布局
function AuthLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout, activeCourse } = useAuth()
  const { mode, setMode, resolved } = useTheme()
  const activeCoursePath = activeCourse?.id ? `/course/${activeCourse.id}` : '/courses'
  const navItems = [
    { label: '学习首页', path: '/home', match: (p) => p === '/home', icon: <ReadOutlined /> },
    { label: '学习路径', path: activeCourse?.id ? `/course/${activeCourse.id}/path` : '/courses', match: (p) => p.includes('/path') || p.includes('/stage/') || p.includes('/task/') || p.includes('/learn/') || p.includes('/classroom/'), icon: <BranchesOutlined /> },
    { label: 'AI 学习助手', path: activeCourse?.id ? `/course/${activeCourse.id}/ai-workspace` : '/ai-workspace', match: (p) => p.includes('/ai-workspace') || p.includes('/chat'), icon: <RobotOutlined /> },
    { label: '学习评估', path: '/assessment/dashboard', match: (p) => p.startsWith('/assessment') || p.includes('/assessment') || p.includes('/test') || p === '/evaluate', icon: <CheckCircleOutlined /> },
    { label: '我的学习资料', path: '/resources', match: (p) => p === '/resources' || p.startsWith('/resources?') || p.startsWith('/resources/'), icon: <FileTextOutlined /> },
  ]

  // 用户下拉菜单项
  const userMenuItems = [
    {
      key: 'user-info',
      label: (
        <div style={{ padding: '4px 0', cursor: 'default' }}>
          <Text strong>{user?.name || user?.username}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>{user?.email || user?.phone || ''}</Text>
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'edit-profile',
      icon: <EditOutlined />,
      label: '修改信息',
      onClick: () => navigate('/edit-profile'),
    },
    {
      key: 'change-password',
      icon: <KeyOutlined />,
      label: '修改密码',
      onClick: () => navigate('/change-password'),
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
    <TutorProvider>
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-page)' }}>
      {/* 顶部导航栏 */}
      <div className="top-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <Text strong style={{ color: 'var(--text-primary)', fontSize: 18, cursor: 'pointer' }} onClick={() => navigate('/home')}>
            🤖 智能学习平台
          </Text>
          {navItems.map((item) => {
            const active = item.match(location.pathname)
            return (
              <span
                key={item.label}
                onClick={() => navigate(item.path)}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 4,
                  fontSize: 14,
                  color: active ? '#6C5CE7' : 'var(--text-secondary)',
                  fontWeight: active ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'color 0.2s',
                  userSelect: 'none',
                }}
                onMouseEnter={(e) => { if (!active) e.currentTarget.style.color = '#6C5CE7' }}
                onMouseLeave={(e) => { if (!active) e.currentTarget.style.color = 'var(--text-secondary)' }}
              >
                {item.icon} {item.label}
              </span>
            )
          })}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* 通知 */}
          <NotificationCenter />

          {/* 主题切换 */}
          <Dropdown menu={{
            items: Object.values(THEMES).map((t) => {
              const iconEl =
                t.icon === 'sun' ? <SunOutlined /> :
                t.icon === 'moon' ? <MoonOutlined /> :
                <DesktopOutlined />
              return {
                key: t.key,
                icon: iconEl,
                label: t.label,
                onClick: () => setMode(t.key),
              }
            }),
            selectedKeys: [mode],
          }} placement="bottomRight" trigger={['click']}>
            <div className="top-home-btn" title="主题切换">
              {mode === 'auto'
                ? <DesktopOutlined />
                : resolved === 'dark'
                  ? <MoonOutlined />
                  : <SunOutlined />
              }
            </div>
          </Dropdown>

          {/* 个人中心 */}
          <div
            className="top-home-btn"
            title="当前课程"
            onClick={() => navigate(activeCoursePath)}
            style={{
              color: location.pathname.startsWith('/course/') ? '#6C5CE7' : undefined,
            }}
          >
            <BookOutlined />
          </div>

          {/* 用户头像下拉 */}
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" trigger={['click']}>
            <div className="top-user-btn">
              <Avatar size={30} icon={<UserOutlined />} src={user?.avatar} style={{ backgroundColor: '#1677ff' }} />
              <span className="top-user-name">{user?.name || user?.username}</span>
            </div>
          </Dropdown>
        </div>
      </div>

      {/* 内容区（全宽） */}
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
        <Suspense fallback={<LoadingSkeleton type="detail" />}>
          <Routes>
            <Route path="/" element={<Navigate to="/home" replace />} />
            <Route path="/home" element={<HomePage />} />
            <Route path="/courses" element={<CourseEntryPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/onboarding/profile" element={<ProfileSetupPage mode="setup" />} />
            <Route path="/ai-workspace" element={<AIWorkspacePage />} />
            <Route path="/generating" element={<Navigate to={activeCourse?.id ? `/course/${activeCourse.id}/ai-workspace` : '/ai-workspace'} replace />} />
            <Route path="/resources/generate" element={<Navigate to={activeCourse?.id ? `/course/${activeCourse.id}/ai-workspace` : '/ai-workspace'} replace />} />
            <Route path="/study" element={<Navigate to="/home" replace />} />
            <Route path="/course/:courseId" element={<CourseScopedRoute><StudyHomePage /></CourseScopedRoute>} />
            <Route path="/course/:courseId/learn/:taskId" element={<CourseScopedRoute><StageResourcePage /></CourseScopedRoute>} />
            <Route path="/course/:courseId/classroom/:classroomId" element={<InteractiveClassroomPage />} />
            <Route path="/course/:courseId/profile/setup" element={<CourseScopedRoute><ProfileSetupPage mode="setup" /></CourseScopedRoute>} />
            <Route path="/course/:courseId/profile" element={<CourseScopedRoute><ProfileSetupPage mode="view" /></CourseScopedRoute>} />
            <Route path="/course/:courseId/profile/update" element={<CourseScopedRoute><ProfileSetupPage mode="update" /></CourseScopedRoute>} />
            <Route path="/course/:courseId/path/generating" element={<CourseScopedRoute><ProfileSetupPage mode="setup" /></CourseScopedRoute>} />
            <Route path="/course/:courseId/ai-workspace" element={<CourseScopedRoute><AIWorkspacePage /></CourseScopedRoute>} />
            <Route path="/course/:courseId/path" element={<CourseScopedRoute><LearningJourneyPage /></CourseScopedRoute>} />
            <Route path="/course/:courseId/graph" element={<CourseScopedRoute><LearningJourneyPage /></CourseScopedRoute>} />
            <Route path="/course/:courseId/stage/:stageId" element={<CourseScopedRoute><StageResourcePage /></CourseScopedRoute>} />
            <Route path="/course/:courseId/chat" element={<CourseScopedRoute><AIWorkspacePage /></CourseScopedRoute>} />
            <Route path="/course/:courseId/test" element={<CourseScopedRoute><EvaluatePage /></CourseScopedRoute>} />
            <Route path="/course/:courseId/assessment/report" element={<CourseScopedRoute><EvaluatePage /></CourseScopedRoute>} />
            <Route path="/course/:courseId/wrongbook" element={<CourseScopedRoute><WrongBookPage /></CourseScopedRoute>} />
            <Route path="/landing" element={<LandingPage />} />

            <Route path="/docs" element={<DocsPage />} />
            <Route path="/assessment/dashboard" element={<LearningAssessmentPage />} />
            <Route path="/assessment/tests" element={<LearningAssessmentPage />} />
            <Route path="/assessment/report" element={<EvaluatePage />} />
            <Route path="/assessment/report/:reportId" element={<EvaluatePage />} />
            <Route path="/assessment/history" element={<EvaluatePage />} />
            <Route path="/evaluate" element={<Navigate to="/assessment/tests" replace />} />
            <Route path="/resources/:resourceId" element={<ResourceDetailPage />} />
            <Route path="/resources" element={<ResourcePage />} />
            <Route path="/learning-path/:pathId" element={<LearningPathPage />} />
            <Route path="/edit-profile" element={<EditProfilePage />} />
            <Route path="/change-password" element={<ChangePasswordPage />} />
            <Route path="/code-practice" element={<CodePracticePage />} />
            <Route path="/code-practice/:problemId" element={<CodePracticePage />} />
            <Route path="/code-experiment" element={<CodeExperimentPage />} />
            <Route path="/code-experiment/:experimentId" element={<CodeExperimentPage />} />
          </Routes>
        </Suspense>
        <FloatingTutor />
      </div>
    </div>
    </TutorProvider>
  )
}

// 路由守卫：未登录重定向到登录页
function RequireAuth({ children }) {
  const { isLoggedIn } = useAuth()
  if (!isLoggedIn) return <Navigate to="/login" replace />
  return children
}

function CourseScopedRoute({ children }) {
  const { courseId } = useParams()
  const { activeCourse, activateCourse } = useAuth()

  useEffect(() => {
    if (!courseId) return
    if (String(activeCourse?.id || '') === String(courseId)) return
    activateCourse(courseId).catch(() => {})
  }, [activateCourse, activeCourse?.id, courseId])

  return <PageErrorBoundary>{children}</PageErrorBoundary>
}

export default function App() {
  return (
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
  )
}
