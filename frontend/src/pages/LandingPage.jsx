import { Row, Col, Card, Typography, Space, Button, Steps, message } from 'antd'
import {
  RobotOutlined,
  BookOutlined,
  CompassOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  AimOutlined,
  MessageOutlined,
  ReadOutlined,
  RocketOutlined,
  UserOutlined,
  BulbOutlined,
  SafetyOutlined,
  StarOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const { Title, Text, Paragraph } = Typography

// 核心功能
const MODULES = [
  { key: 'profile', icon: <BarChartOutlined />, title: '学习画像', desc: '六维雷达图 + 评分趋势，全面掌握学习状态与进步轨迹', route: '/home', color: '#fa8c16' },
  { key: 'resource', icon: <BookOutlined />, title: '学习资源', desc: '海量资源库，涵盖文档、练习题、思维导图，支持 AI 智能生成', route: '/resources', color: '#1677ff' },
  { key: 'path', icon: <CompassOutlined />, title: '学习路径', desc: 'AI 根据学习画像定制个性化路线，分阶段达成学习目标', route: '/learning-path/1', color: '#52c41a' },
  { key: 'tutor', icon: <RobotOutlined />, title: '智能辅导', desc: 'AI 辅导老师随时待命，解答疑问、批改作业，提供个性化学习建议', route: '/', color: '#8b5cf6' },
  { key: 'evaluate', icon: <TrophyOutlined />, title: '学习评估', desc: '综合评分 + 知识点掌握度分析，精准定位强弱项，追踪学习趋势', route: '/home', color: '#eb2f96' },
]

// 亮点
const HIGHLIGHTS = [
  { icon: <ThunderboltOutlined />, title: 'AI 驱动', desc: '大语言模型驱动的智能分析与辅导' },
  { icon: <AimOutlined />, title: '个性化路径', desc: '因人而异的自适应学习规划引擎' },
  { icon: <MessageOutlined />, title: '实时对话', desc: '流式 SSE 对话，即时答疑解惑' },
  { icon: <ReadOutlined />, title: '多元资源', desc: '文档、习题、思维导图全类型覆盖' },
  { icon: <RocketOutlined />, title: '高效提升', desc: '数据驱动的精准学习建议与反馈' },
  { icon: <SafetyOutlined />, title: '全程陪伴', desc: '实时跟踪进度，智能督促执行' },
]

// 工作流
const WORKFLOW = [
  { icon: <UserOutlined />, color: '#8b5cf6', title: '创建学习画像', desc: '录入基本信息，AI 分析学习风格与基础水平' },
  { icon: <BulbOutlined />, color: '#1677ff', title: '智能诊断', desc: '问答与测试，精准定位优势与薄弱环节' },
  { icon: <CompassOutlined />, color: '#52c41a', title: '生成学习路径', desc: '量身定制阶段性学习路线图' },
  { icon: <RobotOutlined />, color: '#fa8c16', title: '辅导执行', desc: 'AI 辅导 + 资源推荐，按路径逐步推进' },
  { icon: <BarChartOutlined />, color: '#eb2f96', title: '评估反馈', desc: '持续跟踪评分趋势，动态调整策略' },
]

// 技术栈
const TECH_STACK = [
  { label: '前端框架', value: 'React 18 + Ant Design 5', icon: <CheckCircleOutlined />, color: '#1677ff' },
  { label: 'AI 模型', value: 'Claude / GPT 大语言模型', icon: <StarOutlined />, color: '#8b5cf6' },
  { label: '后端服务', value: 'Python Flask + SSE 流式', icon: <ThunderboltOutlined />, color: '#52c41a' },
  { label: '数据可视化', value: 'ECharts + D3.js', icon: <BarChartOutlined />, color: '#fa8c16' },
]

// 统一的段落标题字号
const TITLE_FONT_SIZE = 28

export default function LandingPage() {
  const navigate = useNavigate()
  const { isLoggedIn } = useAuth()

  // 登录校验跳转
  function safeNavigate(path) {
    if (!isLoggedIn) {
      message.warning('请先登录后再继续操作')
      navigate('/login', { replace: true })
      return
    }
    navigate(path)
  }

  return (
    <div style={{ maxWidth: 1060, margin: '0 auto', padding: '0 24px 56px' }}>
      {/* ==================== Hero ==================== */}
      <div
        className="home-hero"
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 48,
          borderRadius: 24,
          padding: '56px 56px 56px 60px',
          marginTop: 20,
          marginBottom: 60,
          background: 'linear-gradient(135deg, #0b0a20 0%, #181440 40%, #0c1a3a 100%)',
          overflow: 'hidden',
          boxShadow: '0 8px 48px rgba(99,102,241,0.25)',
        }}
      >
        {/* 装饰 */}
        <div className="hero-bg-glow" style={{ position: 'absolute', top: -80, right: -60, width: 360, height: 360, borderRadius: '50%', background: 'radial-gradient(circle, rgba(139,92,246,0.28) 0%, rgba(99,102,241,0.06) 50%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: -100, left: -40, width: 300, height: 300, borderRadius: '50%', background: 'radial-gradient(circle, rgba(59,130,246,0.18) 0%, transparent 60%)', pointerEvents: 'none' }} />
        <div className="hero-grid" style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)', backgroundSize: '56px 56px', pointerEvents: 'none' }} />

        {/* 左侧文字 */}
        <div style={{ position: 'relative', zIndex: 1, flex: '1 1 auto', maxWidth: 520 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '4px 14px', borderRadius: 20, background: 'rgba(139,92,246,0.18)', border: '1px solid rgba(139,92,246,0.3)', marginBottom: 20 }}>
            <StarOutlined style={{ color: '#c4b5fd', fontSize: 13 }} />
            <Text style={{ color: '#c4b5fd', fontSize: 13, fontWeight: 500 }}>AI 驱动的下一代学习平台</Text>
          </div>

          <Title style={{ color: '#f8f7ff', fontWeight: 800, fontSize: 40, lineHeight: 1.25, marginBottom: 16, letterSpacing: -0.5 }}>
            智能学习
            <span style={{ background: 'linear-gradient(135deg, #c084fc, #818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}> 从此开始</span>
          </Title>

          <Paragraph style={{ color: 'rgba(255,255,255,0.65)', fontSize: 16, lineHeight: 1.8, marginBottom: 32, maxWidth: 440 }}>
            融合 AI 智能辅导、个性化资源推荐、自适应路径规划
            与六维学习画像，为你打造专属的学习体验。
          </Paragraph>

          <Space size="middle">
            <Button type="primary" size="large" icon={<RocketOutlined />}
              onClick={() => safeNavigate('/')}
              className="hero-cta-primary"
              style={{
                height: 46, borderRadius: 12, fontWeight: 600, fontSize: 15,
                padding: '0 28px', background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
                border: 'none', boxShadow: '0 4px 20px rgba(139,92,246,0.4)',
              }}>
              开始学习
            </Button>
            <Button ghost size="large" icon={<BarChartOutlined />}
              onClick={() => safeNavigate('/home')}
              style={{
                height: 46, borderRadius: 12, fontWeight: 500, fontSize: 15,
                borderColor: 'rgba(255,255,255,0.3)', color: 'rgba(255,255,255,0.85)',
              }}>
              查看画像
            </Button>
          </Space>
        </div>

        {/* 右侧装饰图标 */}
        <div className="hero-icon-block" style={{
          position: 'relative', zIndex: 1, flexShrink: 0,
          width: 200, height: 200, borderRadius: 32,
          background: 'linear-gradient(135deg, rgba(139,92,246,0.2), rgba(99,102,241,0.1))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 0 60px rgba(139,92,246,0.25)',
        }}>
          <RobotOutlined style={{ fontSize: 80, color: '#c4b5fd' }} />
        </div>
      </div>

      {/* ==================== 核心功能 ==================== */}
      <div style={{ marginBottom: 64 }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <Title level={2} style={{ fontSize: TITLE_FONT_SIZE, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
            核心功能
          </Title>
          <Text type="secondary" style={{ fontSize: 16 }}>五大模块协同工作，为你提供完整的学习闭环</Text>
        </div>

        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          {MODULES.map((mod) => (
            <div key={mod.key} style={{ flex: '1 1 180px', minWidth: 0 }}>
              <Card
                hoverable
                className="home-module-card"
                style={{
                  borderRadius: 16, height: '100%', border: 'none', boxShadow: 'none',
                  overflow: 'hidden', cursor: 'pointer',
                }}
                styles={{ body: { padding: '28px 24px 24px', display: 'flex', flexDirection: 'column' } }}
              >
                <div className="home-module-icon" style={{
                  width: 56, height: 56, borderRadius: 16,
                  background: `${mod.color}12`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  marginBottom: 20, fontSize: 26, color: mod.color,
                  transition: 'transform 0.3s, box-shadow 0.3s',
                }}>
                  {mod.icon}
                </div>

                <Title level={5} style={{ color: 'var(--text-primary)', marginBottom: 10, fontWeight: 600, fontSize: 17 }}>
                  {mod.title}
                </Title>
                <Text type="secondary" style={{ fontSize: 14, lineHeight: 1.7, flex: 1 }}>
                  {mod.desc}
                </Text>

              </Card>
            </div>
          ))}
        </div>
      </div>

      {/* ==================== 学习流程 ==================== */}
      <div style={{ marginBottom: 64 }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <Title level={2} style={{ fontSize: TITLE_FONT_SIZE, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
            学习流程
          </Title>
          <Text type="secondary" style={{ fontSize: 16 }}>五步开启智能学习，从画像创建到持续进步</Text>
        </div>

        <Steps
          current={-1}
          size="small"
          items={WORKFLOW.map((step) => ({
            title: step.title,
            description: step.desc,
            icon: (
              <div style={{
                width: 28, height: 28, borderRadius: 8, display: 'flex',
                alignItems: 'center', justifyContent: 'center',
                background: `${step.color}15`, color: step.color, fontSize: 14,
              }}>
                {step.icon}
              </div>
            ),
          }))}
          style={{ maxWidth: 900, margin: '0 auto' }}
        />
      </div>

      {/* ==================== 平台亮点 ==================== */}
      <div style={{ marginBottom: 64 }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <Title level={2} style={{ fontSize: TITLE_FONT_SIZE, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
            平台亮点
          </Title>
          <Text type="secondary" style={{ fontSize: 16 }}>六位一体的智能引擎，全方位保障学习效果</Text>
        </div>

        <Row gutter={[16, 16]}>
          {HIGHLIGHTS.map((h, i) => (
            <Col xs={24} sm={12} md={8} lg={4} key={i}>
              <div className="home-highlight-card"
                style={{
                  padding: '28px 16px 22px', borderRadius: 14, textAlign: 'center',
                  background: 'var(--bg-card, #fff)',
                  height: '100%', transition: 'all 0.3s',
                }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 14, display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 14px', fontSize: 22, color: '#8b5cf6',
                  background: 'linear-gradient(135deg, #f5f3ff, #ede9fe)',
                }}>
                  {h.icon}
                </div>
                <Text strong style={{ fontSize: 15, display: 'block', marginBottom: 6, color: 'var(--text-primary)' }}>
                  {h.title}
                </Text>
                <Text type="secondary" style={{ fontSize: 13, lineHeight: 1.6 }}>
                  {h.desc}
                </Text>
              </div>
            </Col>
          ))}
        </Row>
      </div>

      {/* ==================== 技术栈 ==================== */}
      <div style={{ textAlign: 'center' }}>
        <Title level={2} style={{ fontSize: TITLE_FONT_SIZE, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
          技术架构
        </Title>
        <Text type="secondary" style={{ fontSize: 16, display: 'block', marginBottom: 36 }}>
          构建于现代技术栈之上
        </Text>

        <Row gutter={[16, 16]} justify="center">
          {TECH_STACK.map((tech) => (
            <Col xs={24} sm={12} md={6} key={tech.label}>
              <div className="home-tech-item" style={{
                padding: '24px 16px', borderRadius: 14,
                background: 'var(--bg-chat, #f9f9fb)',
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10, display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 12px', background: `${tech.color}15`,
                  color: tech.color, fontSize: 18,
                }}>
                  {tech.icon}
                </div>
                <Text strong style={{ fontSize: 15, display: 'block', marginBottom: 4, color: 'var(--text-primary)' }}>
                  {tech.value}
                </Text>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  {tech.label}
                </Text>
              </div>
            </Col>
          ))}
        </Row>
      </div>
    </div>
  )
}
