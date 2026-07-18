import { Card, Empty, Tag, Typography } from 'antd'
import {
  BulbOutlined,
  CodeOutlined,
  CommentOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  FormOutlined,
  ReadOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import IntroductionScene from './IntroductionScene'
import PresentationScene from './PresentationScene'
import WhiteboardScene from './WhiteboardScene'
import SimulationScene from './SimulationScene'
import DiscussionScene from './DiscussionScene'
import QuizScene from './QuizScene'
import CodeDemoScene from './CodeDemoScene'
import SummaryScene from './SummaryScene'
import MarkdownRenderer from '../MarkdownRenderer'
import MindMapViewer from '../MindMapViewer'

const { Title, Text } = Typography

const SCENE_META = {
  introduction: { label: '导入', icon: <BulbOutlined /> },
  presentation: { label: '讲授', icon: <ReadOutlined /> },
  whiteboard: { label: '图解', icon: <FileTextOutlined /> },
  simulation: { label: '模拟实验', icon: <ExperimentOutlined /> },
  discussion: { label: '讨论', icon: <CommentOutlined /> },
  quiz: { label: '知识检查', icon: <FormOutlined /> },
  code_demo: { label: '代码演示', icon: <CodeOutlined /> },
  summary: { label: '总结', icon: <TrophyOutlined /> },
}

/** Convert scene content to a markdown string for lecture view */
function sceneToMarkdown(scene) {
  if (!scene) return ''
  const lines = [`# ${scene.title || ''}`, '']
  if (scene.description) {
    lines.push(scene.description, '')
  }
  const content = scene.content
  if (content) {
    if (content.objectives?.length) {
      lines.push('## 学习目标', '')
      content.objectives.forEach((o) => lines.push(`- ${o}`))
      lines.push('')
    }
    if (content.slides?.length) {
      lines.push('## 内容讲解', '')
      content.slides.forEach((slide) => {
        if (slide.title) lines.push(`### ${slide.title}`, '')
        if (slide.points?.length) {
          slide.points.forEach((p) => lines.push(`- ${p}`))
          lines.push('')
        }
        if (slide.text) lines.push(slide.text, '')
      })
    }
    if (content.key_points?.length) {
      lines.push('## 重点归纳', '')
      content.key_points.forEach((p) => lines.push(`- ${p}`))
      lines.push('')
    }
  }
  if (lines.length <= 2) lines.push('暂无详细讲义内容')
  return lines.join('\n')
}

/** Render scene content in non-slide view formats */
function renderContentView(scene, contentView, classroom, session, onSimulationActionsChange) {
  switch (contentView) {
    case 'lecture': {
      const md = sceneToMarkdown(scene)
      return (
        <div style={{ padding: '24px 32px', overflow: 'auto', height: '100%' }}>
          <MarkdownRenderer content={md} />
        </div>
      )
    }
    case 'mindmap': {
      const markdown = sceneToMarkdown(scene)
      return (
        <div style={{ width: '100%', height: '100%' }}>
          <MindMapViewer content={markdown} />
        </div>
      )
    }
    case 'code':
      return <CodeDemoScene scene={scene} />
    case 'quiz':
      return <QuizScene scene={scene} classroom={classroom} session={session} />
    default:
      // Fallback to slide view
      return renderSlideView(scene, onSimulationActionsChange, classroom, session)
  }
}

function renderSlideView(scene, onSimulationActionsChange, classroom, session) {
  switch (scene.scene_type) {
    case 'introduction': return <IntroductionScene scene={scene} />
    case 'presentation': return <PresentationScene scene={scene} />
    case 'whiteboard': return <WhiteboardScene scene={scene} />
    case 'simulation': return <SimulationScene scene={scene} onActionsChange={onSimulationActionsChange} />
    case 'discussion': return <DiscussionScene scene={scene} />
    case 'quiz': return <QuizScene scene={scene} classroom={classroom} session={session} />
    case 'code_demo': return <CodeDemoScene scene={scene} />
    case 'summary': return <SummaryScene scene={scene} />
    default: return <PresentationScene scene={scene} />
  }
}

export default function InteractiveClassroomCanvas({
  scene,
  sceneIndex,
  totalScenes,
  classroom,
  session,
  contentView = 'slide',
  onSimulationActionsChange,
}) {
  if (!scene) {
    return (
      <Card className="classroom-canvas">
        <Empty description="暂无课堂场景" />
      </Card>
    )
  }

  const meta = SCENE_META[scene.scene_type] || SCENE_META.presentation

  return (
    <Card
      className="classroom-canvas"
      styles={{
        body: { height: '100%', display: 'flex', flexDirection: 'column', padding: 0 },
      }}
    >
      {/* Header — hidden in non-slide views to maximize content space */}
      {contentView === 'slide' && (
        <div className="classroom-canvas-head" style={{ padding: '16px 24px', borderBottom: '1px solid rgba(0,0,0,0.04)' }}>
          <div>
            <Tag color="purple" icon={meta.icon}>{meta.label}</Tag>
            <Title level={4} style={{ margin: '8px 0 4px' }}>{scene.title}</Title>
            <Text type="secondary">
              场景 {sceneIndex + 1} / {totalScenes}
              {scene.estimated_minutes && ` · 预计 ${scene.estimated_minutes} 分钟`}
            </Text>
          </div>
        </div>
      )}

      <div className="classroom-canvas-body" style={{ flex: 1, minHeight: 0 }}>
        {contentView === 'slide'
          ? renderSlideView(scene, onSimulationActionsChange, classroom, session)
          : renderContentView(scene, contentView, classroom, session, onSimulationActionsChange)
        }
      </div>
    </Card>
  )
}
