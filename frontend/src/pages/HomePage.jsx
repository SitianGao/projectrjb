import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Avatar, Button, Card, Dropdown, Empty, Progress, Skeleton, Space, Statistic, Tag, Typography, message,
} from 'antd'
import {
  AppstoreOutlined, BookOutlined, BranchesOutlined, CheckCircleOutlined,
  CodeOutlined, ExperimentOutlined, FileTextOutlined, MessageOutlined,
  PlayCircleOutlined, PlusOutlined, ProfileOutlined, ReadOutlined,
  ReloadOutlined, RightOutlined, SwapOutlined, ThunderboltOutlined,
} from '@ant-design/icons'
import { getCourseDashboard } from '../api/courses'
import { useAuth } from '../contexts/AuthContext'
import './HomePage.css'

const { Title, Text, Paragraph } = Typography

// ── helpers ──

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
}

function isMeaningfulCourse(course) {
  const title = String(course?.title || '').trim().toLowerCase()
  if (!title) return false
  if (title === 'shux' || title === 'vjg') return false
  if (/^待命名课程/.test(course?.title || '')) return false
  return true
}

function uniqueCourses(courses = []) {
  const seen = new Set()
  return courses.filter((course) => {
    if (!isMeaningfulCourse(course)) return false
    const key = `${String(course.title || '').trim()}::${String(course.goal || '').trim()}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

// ── button config by course status ──

const STATUS_ACTIONS = {
  api_error: {
    primary: { text: '重新加载', icon: <ReloadOutlined /> },
    secondary: null,
    primaryRoute: () => window.location.reload(),
    secondaryRoute: () => {},
  },
  profile_incomplete: {
    primary: { text: '完善课程画像', icon: <ThunderboltOutlined /> },
    secondary: { text: '问 AI 导师', icon: <MessageOutlined /> },
    primaryRoute: (course) => `/course/${course.id}/profile/setup`,
    secondaryRoute: (course) => `/course/${course.id}/ai-workspace`,
  },
  path_missing: {
    primary: { text: '生成学习路径', icon: <ThunderboltOutlined /> },
    secondary: { text: '查看画像', icon: <MessageOutlined /> },
    primaryRoute: (course) => `/course/${course.id}/profile/setup`,
    secondaryRoute: (course) => `/course/${course.id}/profile/setup`,
  },
  path_not_generated: {
    primary: { text: '完善课程画像', icon: <ThunderboltOutlined /> },
    secondary: { text: '问 AI 导师', icon: <MessageOutlined /> },
    primaryRoute: (course) => `/course/${course.id}/profile/setup`,
    secondaryRoute: (course) => `/course/${course.id}/ai-workspace`,
  },
  not_started: {
    primary: { text: '开始学习', icon: <PlayCircleOutlined /> },
    secondary: { text: '查看学习路径', icon: <BranchesOutlined /> },
    primaryRoute: (course) => `/course/${course.id}/path`,
    secondaryRoute: (course) => `/course/${course.id}/path`,
  },
  in_progress: {
    primary: { text: '继续学习', icon: <PlayCircleOutlined /> },
    secondary: { text: '问 AI 导师', icon: <MessageOutlined /> },
    primaryRoute: (course, dash) => dash?.current_task?.task_id
      ? `/course/${course.id}/learn/${encodeURIComponent(dash.current_task.task_id)}`
      : `/course/${course.id}/path`,
    secondaryRoute: (course) => `/course/${course.id}/ai-workspace`,
  },
  completed: {
    primary: { text: '查看课程总结', icon: <CheckCircleOutlined /> },
    secondary: { text: '复习错题', icon: <ReloadOutlined /> },
    primaryRoute: (course) => `/course/${course.id}/assessment/report`,
    secondaryRoute: (course) => `/course/${course.id}/wrongbook`,
  },
}

// ── status descriptions ──

function getStatusDescription(status, stage) {
  switch (status) {
    case 'api_error':
      return '学习数据加载失败，请点击重新加载或刷新页面。'
    case 'profile_incomplete':
      return '和 AI 聊聊你的学习目标和基础，系统将为你生成专属学习路径。'
    case 'path_missing':
    case 'path_not_generated':
      return '画像已完善！点击生成学习路径，AI 将为你规划专属阶段和资源。'
    case 'not_started':
      return `学习路径已就绪，从「${stage?.title || '第一阶段'}」开始你的学习之旅。`
    case 'in_progress':
      return `当前章节：${stage?.title || '学习中'}。建议本次学习 25 分钟，完成一份讲义和一组练习后再进入测评。`
    case 'completed':
      return '恭喜！你已完成本课程全部学习内容。查看总结或开始复习巩固。'
    default:
      return ''
  }
}

// ── sub-components ──

function CourseShortcut({ icon, title, desc, color, onClick }) {
  return (
    <Card className="dashboard-shortcut" hoverable onClick={onClick}>
      <div className="shortcut-inner">
        <span className="shortcut-icon" style={{ color, background: `${color}14` }}>{icon}</span>
        <div>
          <Text strong>{title}</Text>
          <Paragraph>{desc}</Paragraph>
        </div>
        <RightOutlined className="shortcut-arrow" />
      </div>
    </Card>
  )
}

function HeroStat({ title, value, suffix, prefix, emptyLabel }) {
  const hasValue = value !== null && value !== undefined && value !== '--' && value !== 0
  return (
    <div className="hero-stat-item">
      {hasValue ? (
        <Statistic title={title} value={value} suffix={suffix} prefix={prefix} />
      ) : (
        <div className="hero-stat-empty">
          <Text type="secondary" style={{ fontSize: 12 }}>{title}</Text>
          <Text type="secondary" style={{ fontSize: 13 }}>{emptyLabel || '暂无记录'}</Text>
        </div>
      )}
    </div>
  )
}

// ── main page ──

export default function HomePage() {
  const navigate = useNavigate()
  const { user, courses, activeCourse, activateCourse, createCourse } = useAuth()

  const [loading, setLoading] = useState(true)
  const [switching, setSwitching] = useState(false)
  const [dashboard, setDashboard] = useState(null)
  const [dashboardError, setDashboardError] = useState(false)

  const cleanCourses = useMemo(() => uniqueCourses(courses), [courses])
  const currentCourse = useMemo(() => {
    if (activeCourse && isMeaningfulCourse(activeCourse)) return activeCourse
    return cleanCourses[0] || null
  }, [activeCourse, cleanCourses])

  const loadDashboard = useCallback(async () => {
    if (!currentCourse?.id) { setDashboard(null); setLoading(false); return }
    setLoading(true); setDashboardError(false)
    try {
      const data = await getCourseDashboard(currentCourse.id)
      setDashboard(data)
    } catch {
      setDashboard(null); setDashboardError(true)
    } finally { setLoading(false) }
  }, [currentCourse])

  useEffect(() => {
    const timer = window.setTimeout(() => loadDashboard(), 0)
    return () => window.clearTimeout(timer)
  }, [loadDashboard])

  const handleSwitchCourse = useCallback(async (course) => {
    if (!course || course.id === currentCourse?.id) return
    setSwitching(true)
    try { await activateCourse(course.id); message.success(`已切换到「${course.title}」`) }
    catch { message.error('课程切换失败') }
    finally { setSwitching(false) }
  }, [activateCourse, currentCourse?.id])

  const handleCreateCourse = useCallback(async () => {
    try { await createCourse(`新课程 ${cleanCourses.length + 1}`, '') }
    catch { /* createCourse already shows error toast */ }
  }, [cleanCourses.length, createCourse])

  // ── derived state ──

  const courseStatus = dashboard?.course_status || dashboard?.course?.status || (dashboardError ? 'api_error' : 'path_not_generated')
  const normalizedStatus =
    courseStatus === 'path_not_generated' ? 'profile_incomplete'
    : courseStatus === 'learning' ? 'in_progress'
    : courseStatus
  const action = STATUS_ACTIONS[normalizedStatus] || STATUS_ACTIONS.profile_incomplete
  const progress = dashboard?.progress || {}
  const currentStage = dashboard?.current_stage

  const courseMenuItems = [
    ...cleanCourses.map((c) => ({
      key: c.id,
      label: (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', minWidth: 180 }}>
          <Space>
            <Avatar size={24} style={{ background: c.id === currentCourse?.id ? '#6C5CE7' : '#D1D5DB', fontSize: 12 }}>
              {c.title?.slice(0, 1)}
            </Avatar>
            <span style={{ fontWeight: c.id === currentCourse?.id ? 600 : 400 }}>{c.title}</span>
          </Space>
          {c.id === currentCourse?.id && <CheckCircleOutlined style={{ color: '#6C5CE7', fontSize: 14 }} />}
        </div>
      ),
      onClick: () => handleSwitchCourse(c),
    })),
    { type: 'divider' },
    { key: 'all-courses', icon: <AppstoreOutlined />, label: '查看全部课程', onClick: () => navigate('/courses') },
    { key: 'create-course', icon: <PlusOutlined />, label: '创建新课程', onClick: handleCreateCourse },
  ]

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        {loading && !dashboard ? (
          <Skeleton active paragraph={{ rows: 10 }} />
        ) : (
          <>
            {/* ── Hero Section ── */}
            <section className="dashboard-hero">
              <div className="hero-copy">
                <Tag color="purple">个性化学习首页</Tag>
                <Title level={1}>{getGreeting()}，{user?.name || user?.username || '同学'}</Title>

                {currentCourse ? (
                  <>
                    <Text className="hero-meta">当前课程</Text>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}>
                      <Title level={3} style={{ margin: 0 }}>{currentCourse.title}</Title>
                      <Dropdown menu={{ items: courseMenuItems }} trigger={['click']} placement="bottomLeft">
                        <Button type="text" size="small"
                          icon={switching ? undefined : <SwapOutlined />} loading={switching}
                          style={{ color: '#6C5CE7', fontWeight: 600, fontSize: 13 }}>
                          切换课程
                        </Button>
                      </Dropdown>
                    </div>
                    <Paragraph style={{ minHeight: 44, marginBottom: 12 }}>
                      {getStatusDescription(normalizedStatus, currentStage)}
                    </Paragraph>
                  </>
                ) : (
                  <>
                    <Paragraph style={{ marginBottom: 12 }}>
                      还没有可学习课程。创建课程后，AI 会根据你的目标生成专属路径和资源。
                    </Paragraph>
                    <Space wrap size={12}>
                      <Button type="primary" size="large" icon={<PlusOutlined />} onClick={handleCreateCourse}>创建第一门课程</Button>
                      <Button size="large" icon={<AppstoreOutlined />} onClick={() => navigate('/courses')}>浏览课程</Button>
                    </Space>
                  </>
                )}

                {currentCourse && (
                  <Space wrap size={12}>
                    <Button type="primary" size="large" icon={action.primary.icon}
                      onClick={() => navigate(action.primaryRoute(currentCourse, dashboard))}>
                      {action.primary.text}
                    </Button>
                    {action.secondary && (
                      <Button size="large" icon={action.secondary.icon}
                        onClick={() => navigate(action.secondaryRoute(currentCourse, dashboard))}>
                        {action.secondary.text}
                      </Button>
                    )}
                  </Space>
                )}
              </div>

              {/* ── Stats Card ── */}
              <Card className="hero-stats">
                {currentCourse ? (
                  normalizedStatus === 'api_error' ? (
                    <div className="hero-guided-empty">
                      <Text strong style={{ fontSize: 15, color: '#374151' }}>数据加载失败</Text>
                      <Paragraph type="secondary" style={{ fontSize: 13, margin: '8px 0 16px' }}>
                        无法获取当前课程的学习状态，请检查网络连接后重试。
                      </Paragraph>
                      <Button type="primary" size="small" icon={<ReloadOutlined />}
                        onClick={() => window.location.reload()} style={{ marginTop: 16, borderRadius: 8 }}>
                        重新加载
                      </Button>
                    </div>
                  ) : (normalizedStatus === 'profile_incomplete' || normalizedStatus === 'path_missing') ? (
                    <div className="hero-guided-empty">
                      <BookOutlined style={{ fontSize: 36, color: '#D1D5DB', marginBottom: 12 }} />
                      <Text strong style={{ fontSize: 15, color: '#374151' }}>{normalizedStatus === 'profile_incomplete' ? '还没有开始这门课程' : '准备生成学习路径'}</Text>
                      <Paragraph type="secondary" style={{ fontSize: 13, margin: '8px 0 16px' }}>
                        完成目标设置后，系统将生成：
                      </Paragraph>
                      <ul style={{ paddingLeft: 20, color: '#6B7280', fontSize: 13, lineHeight: 2, margin: 0 }}>
                        <li>个性化学习路径</li><li>阶段任务</li><li>学习资源</li><li>初始测评</li>
                      </ul>
                      <Button type="primary" size="small" icon={<ThunderboltOutlined />}
                        onClick={() => navigate(`/course/${currentCourse.id}/profile/setup`)}
                        style={{ marginTop: 16, borderRadius: 8 }}>
                        开始设置
                      </Button>
                    </div>
                  ) : (
                    <>
                      <div className="hero-progress">
                        <Text>学习进度</Text>
                        <strong>{progress.percentage || 0}%</strong>
                      </div>
                      <Progress percent={progress.percentage || 0} showInfo={false}
                        strokeColor="#6C5CE7" trailColor="#ECEEF5" />
                      <div className="hero-stat-grid">
                        <HeroStat title="学习时长" value={progress.learning_minutes || 0} suffix="分钟" prefix={<ReadOutlined />} emptyLabel="暂无记录" />
                        <HeroStat title="答题数量" value={progress.answered_questions || 0} suffix="道" prefix={<CheckCircleOutlined />} emptyLabel="暂无记录" />
                        <HeroStat title="连续学习" value={progress.streak_days || 0} suffix="天" prefix={<ThunderboltOutlined />} emptyLabel="暂无记录" />
                        <HeroStat title="完成任务" value={`${progress.completed_tasks || 0}/${progress.total_tasks || 0}`} prefix={<BookOutlined />} emptyLabel="尚未开始" />
                      </div>
                    </>
                  )
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="创建课程后查看学习数据" style={{ margin: '32px 0' }} />
                )}
              </Card>
            </section>

            {/* ── Six Feature Cards ── */}
            <section className="dashboard-shortcuts">
              <CourseShortcut icon={<AppstoreOutlined />} title="AI 学习工作台" desc="课程答疑、资源生成和路径调整" color="#6C5CE7"
                onClick={() => navigate(currentCourse ? `/course/${currentCourse.id}/ai-workspace` : '/courses')} />
              <CourseShortcut icon={<CheckCircleOutlined />} title="在线测评" desc="按当前课程生成评估报告" color="#4F8CFF"
                onClick={() => navigate(currentCourse ? `/course/${currentCourse.id}/assessment/report` : '/assessment/tests')} />
              <CourseShortcut icon={<FileTextOutlined />} title="学习资源" desc="讲义、导图、PPT 和练习题" color="#20C7B7"
                onClick={() => navigate(currentCourse ? `/resources?courseId=${currentCourse.id}` : '/resources')} />
              <CourseShortcut icon={<CodeOutlined />} title="代码挑战" desc="用编程题验证掌握程度" color="#F59E0B"
                onClick={() => navigate('/code-practice')} />
              <CourseShortcut icon={<ExperimentOutlined />} title="代码实验" desc="交互式实验，调参观察结果" color="#89b4fa"
                onClick={() => navigate('/code-experiment')} />
              <CourseShortcut icon={<ProfileOutlined />} title="学习画像" desc="调整目标、基础和学习偏好" color="#EF5DA8"
                onClick={() => navigate(currentCourse ? `/course/${currentCourse.id}/profile/update` : '/profile')} />
              <CourseShortcut icon={<BranchesOutlined />} title="学习路径" desc="查看当前课程阶段路线" color="#7C3AED"
                onClick={() => navigate(currentCourse ? `/course/${currentCourse.id}/path` : '/courses')} />
            </section>

            {/* ── Lower Grid ── */}
            <section className="dashboard-lower-grid">
              <Card className="dashboard-panel" title="个性化学习路径">
                {(() => {
                  const stages = dashboard?.stages || []
                  if (stages.length > 0) {
                    return (
                      <div className="path-preview">
                        {stages.slice(0, 5).map((stage, index) => (
                          <div className="path-preview-row" key={stage.stage_id || index}>
                            <span className={String(stage.stage_id) === String(currentStage?.stage_id) ? 'active' : ''}>{index + 1}</span>
                            <div>
                              <Text strong>{stage.title}</Text>
                              <Paragraph>{stage.description || (stage.topics || []).join('、')}</Paragraph>
                            </div>
                          </div>
                        ))}
                      </div>
                    )
                  }
                  if (normalizedStatus === 'profile_incomplete' || normalizedStatus === 'path_missing') {
                    return (
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={normalizedStatus === 'profile_incomplete' ? '尚未完善课程画像' : '画像已完善，待生成路径'}>
                        <Button type="primary" size="small" icon={<ThunderboltOutlined />}
                          onClick={() => navigate(currentCourse ? `/course/${currentCourse.id}/profile/setup` : '/courses')}>
                          {normalizedStatus === 'profile_incomplete' ? '完善画像' : '生成学习路径'}
                        </Button>
                      </Empty>
                    )
                  }
                  return <Empty description="暂无学习路径" />
                })()}
              </Card>

              <div className="dashboard-side">
                <Card className="dashboard-panel" title="AI 学习建议">
                  {(normalizedStatus === 'profile_incomplete' || normalizedStatus === 'path_missing') ? (
                    <Space direction="vertical" size={12}>
                      <Text>{normalizedStatus === 'profile_incomplete' ? '先完善课程画像，AI 将根据你的目标和基础生成个性化学习路径。' : '画像已完成！点击生成学习路径，获取个性化建议。'}</Text>
                      <Text type="secondary">完成后你可以在这里看到每日学习建议、薄弱点提醒和复习计划。</Text>
                    </Space>
                  ) : normalizedStatus === 'not_started' ? (
                    <Space direction="vertical" size={12}>
                      <Text>路径已生成！从第一阶段开始，每天完成 25 分钟学习任务。</Text>
                      <Text type="secondary">建议先浏览阶段目标，再按顺序完成每项任务。</Text>
                    </Space>
                  ) : normalizedStatus === 'completed' ? (
                    <Space direction="vertical" size={12}>
                      <Text>🎉 课程已全部完成！建议安排定期复习，巩固薄弱知识点。</Text>
                      <Text type="secondary">你可以查看课程总结报告，或开始新一轮学习。</Text>
                    </Space>
                  ) : (
                    <Space direction="vertical" size={12}>
                      <Text>今天优先完成当前章节的核心讲义，再做 3 道检索自测题。</Text>
                      <Text type="secondary">如果正确率低于 70%，建议回到知识图谱查看前置知识点。</Text>
                    </Space>
                  )}
                </Card>

                <Card className="dashboard-panel" title="我的课程">
                  {cleanCourses.length ? (
                    <Space direction="vertical" size={12} style={{ width: '100%' }}>
                      {cleanCourses.slice(0, 4).map((c) => (
                        <button className={`recent-course${c.id === currentCourse?.id ? ' recent-course--active' : ''}`} key={c.id}
                          onClick={() => c.id !== currentCourse?.id ? handleSwitchCourse(c) : navigate(`/course/${c.id}`)}>
                          <Avatar style={{ background: c.id === currentCourse?.id ? '#6C5CE7' : '#D1D5DB' }}>{c.title?.slice(0, 1)}</Avatar>
                          <span>
                            <strong>{c.title}</strong>
                            <Text type="secondary">{c.goal || '继续完善学习目标'}</Text>
                          </span>
                          {c.id === currentCourse?.id ? <Tag color="purple" style={{ borderRadius: 8, margin: 0 }}>当前</Tag> : <RightOutlined />}
                        </button>
                      ))}
                      {cleanCourses.length > 4 && (
                        <Button type="link" block onClick={() => navigate('/courses')}>查看全部 {cleanCourses.length} 门课程</Button>
                      )}
                    </Space>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无课程" />
                  )}
                </Card>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  )
}
