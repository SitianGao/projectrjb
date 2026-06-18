import { useState, useEffect, useRef } from 'react'
import { Typography, Space, Tag, Divider } from 'antd'
import {
  BookOutlined,
  RobotOutlined,
  CompassOutlined,
  BarChartOutlined,
  QuestionCircleOutlined,
  ReadOutlined,
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography

// 使用文档数据
const DOC_SECTIONS = [
  {
    key: 'intro',
    icon: <BookOutlined style={{ color: '#8b5cf6', fontSize: 18 }} />,
    title: '平台简介',
    content: (
      <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
        智能学习平台是一个 AI 驱动的个性化学习系统。它融合了<strong>智能辅导</strong>、<strong>学习资源推荐</strong>、
        <strong>自适应路径规划</strong>与<strong>六维学习画像</strong>四大核心能力，为你打造专属的学习体验。
        无论你是想提升某个学科、备战考试，还是希望系统性地规划学习路线，平台都能根据你的学习画像
        提供精准的个性化服务。
      </Paragraph>
    ),
  },
  {
    key: 'profile',
    icon: <BarChartOutlined style={{ color: '#fa8c16', fontSize: 18 }} />,
    title: '学习画像 — 了解你自己',
    content: (
      <>
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          学习画像是平台的核心基础，它从六个维度全面评估你的学习状态：
        </Paragraph>
        <Space wrap size={[8, 8]} style={{ marginBottom: 16 }}>
          {['知识储备', '学习能力', '思维能力', '学习风格', '学习进度', '目标清晰度'].map((d) => (
            <Tag key={d} color="purple">{d}</Tag>
          ))}
        </Space>
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          每次学习后平台会自动更新画像数据。你可以在主页的<strong>六维雷达图</strong>中直观地看到自己的长板与短板，
          并查看<strong>评分趋势折线图</strong>追踪进步轨迹。
        </Paragraph>
      </>
    ),
  },
  {
    key: 'tutor',
    icon: <RobotOutlined style={{ color: '#8b5cf6', fontSize: 18 }} />,
    title: '智能辅导 — AI 对话学习',
    content: (
      <>
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          智能辅导功能已集成到<strong>个人中心</strong>页面中。你可以：
        </Paragraph>
        <ul style={{ fontSize: 14, lineHeight: 2 }}>
          <li>在个人中心右侧面板找到 AI 辅导老师</li>
          <li>向 AI 辅导老师提问任何学习问题</li>
          <li>上传题目让 AI 帮你分析和解答</li>
          <li>获得针对你薄弱环节的个性化建议</li>
          <li>创建多个辅导会话，按科目或主题分类管理</li>
        </ul>
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          AI 采用<strong>流式 SSE 响应</strong>，打字机效果实时呈现答案，对话体验流畅自然。
        </Paragraph>
      </>
    ),
  },
  {
    key: 'resources',
    icon: <ReadOutlined style={{ color: '#1677ff', fontSize: 18 }} />,
    title: '学习资源 — 知识库',
    content: (
      <>
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          学习资源模块提供多种类型的资源：
        </Paragraph>
        <Space wrap size={[8, 8]} style={{ marginBottom: 16 }}>
          <Tag color="blue">文档</Tag>
          <Tag color="green">练习题</Tag>
          <Tag color="orange">思维导图</Tag>
        </Space>
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          你可以在资源页中浏览和筛选资源。支持关键词搜索和类型过滤，
          点击资源卡片可以查看详情预览。平台还支持<strong>AI 自动生成</strong>定制化学习资源。
        </Paragraph>
      </>
    ),
  },
  {
    key: 'path',
    icon: <CompassOutlined style={{ color: '#52c41a', fontSize: 18 }} />,
    title: '学习路径 — 导航你的进步',
    content: (
      <>
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          学习路径是 AI 根据你的画像<strong>自动生成</strong>的个性化学习路线图。它以时间线形式展示，
          将学习过程分解为多个阶段，每个阶段包含若干具体任务。
        </Paragraph>
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          你可以：
        </Paragraph>
        <ul style={{ fontSize: 14, lineHeight: 2 }}>
          <li>点击<strong>"生成新路径"</strong>让 AI 重新规划</li>
          <li>查看每个阶段的任务清单和资源推荐</li>
          <li>标记任务完成状态，追踪整体进度</li>
          <li>根据评估反馈动态调整学习策略</li>
        </ul>
      </>
    ),
  },
  {
    key: 'faq',
    icon: <QuestionCircleOutlined style={{ color: '#eb2f96', fontSize: 18 }} />,
    title: '常见问题',
    content: (
      <>
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          <strong>Q：如何开始使用？</strong><br />
          登录后进入个人中心（六维画像页面），平台会自动加载你的学习画像。然后在辅导页面与 AI 对话，
          平台会根据对话内容不断优化你的画像和路径。
        </Paragraph>
        <Divider style={{ margin: '16px 0' }} />
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          <strong>Q：数据是真实的吗？</strong><br />
          当前为演示版本，使用 Mock 数据模拟。后续接入真实 API 后将展示实际学习数据。
        </Paragraph>
        <Divider style={{ margin: '16px 0' }} />
        <Paragraph style={{ fontSize: 14, lineHeight: 2 }}>
          <strong>Q：支持哪些学科？</strong><br />
          平台设计为学科无关，任何学科的知识点和题目都可以录入系统。当前演示以数学、物理、英语为主。
        </Paragraph>
      </>
    ),
  },
]

export default function DocsPage() {
  const [activeKey, setActiveKey] = useState('intro')
  const sectionRefs = useRef({})

  // 点击锚点平滑滚动
  function scrollToSection(key) {
    const el = sectionRefs.current[key]
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  // IntersectionObserver 追踪当前可见段落
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveKey(entry.target.id)
            break
          }
        }
      },
      { rootMargin: '-80px 0px -60% 0px', threshold: 0 },
    )

    const refs = sectionRefs.current
    Object.values(refs).forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [])

  return (
    <div style={{ maxWidth: 1060, margin: '0 auto', padding: '24px 24px 48px' }}>
      {/* 标题 */}
      <div style={{ marginBottom: 32 }}>
        <Title level={2} style={{ marginBottom: 8 }}>
          <BookOutlined style={{ color: '#8b5cf6', marginRight: 10 }} />
          使用文档
        </Title>
        <Text type="secondary" style={{ fontSize: 15 }}>
          快速了解平台的各项功能与使用方法
        </Text>
      </div>

      <div style={{ display: 'flex', gap: 48 }}>
        {/* 左侧锚点导航 */}
        <div style={{ flexShrink: 0, width: 250, marginLeft: -12 }}>
          <nav style={{ position: 'sticky', top: 24 }}>
            <Text strong style={{ fontSize: 13, color: '#8c8c8c', marginBottom: 12, display: 'block' }}>
              目录
            </Text>
            {DOC_SECTIONS.map((s) => (
              <div
                key={s.key}
                onClick={() => scrollToSection(s.key)}
                style={{
                  fontSize: 13,
                  padding: '8px 12px',
                  borderRadius: 6,
                  cursor: 'pointer',
                  color: activeKey === s.key ? '#8b5cf6' : 'var(--text-secondary)',
                  fontWeight: activeKey === s.key ? 600 : 400,
                  background: activeKey === s.key ? 'rgba(139,92,246,0.08)' : 'transparent',
                  borderLeft: activeKey === s.key ? '2px solid #8b5cf6' : '2px solid transparent',
                  transition: 'all 0.2s',
                  marginBottom: 2,
                }}
                onMouseEnter={(e) => { if (activeKey !== s.key) e.target.style.color = '#8b5cf6' }}
                onMouseLeave={(e) => { if (activeKey !== s.key) e.target.style.color = 'var(--text-secondary)' }}
              >
                {s.icon}
                <span style={{ marginLeft: 8 }}>{s.title}</span>
              </div>
            ))}
          </nav>
        </div>

        {/* 右侧内容 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {DOC_SECTIONS.map((section) => (
            <div
              key={section.key}
              ref={(el) => { sectionRefs.current[section.key] = el }}
              id={section.key}
              style={{ marginBottom: 40 }}
            >
              {/* 段落标题 */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 10,
                paddingBottom: 12, marginBottom: 16,
                borderBottom: '1px solid var(--border, #f0f0f0)',
              }}>
                {section.icon}
                <Title level={4} style={{ margin: 0 }}>
                  {section.title}
                </Title>
              </div>
              {section.content}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
