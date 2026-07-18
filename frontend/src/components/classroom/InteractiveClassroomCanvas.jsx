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

export default function InteractiveClassroomCanvas({
  scene,
  sceneIndex,
  totalScenes,
  classroom,
  session,
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
    <Card className="classroom-canvas">
      <div className="classroom-canvas-head">
        <div>
          <Tag color="purple" icon={meta.icon}>{meta.label}</Tag>
          <Title level={3}>{scene.title}</Title>
          <Text type="secondary">场景 {sceneIndex + 1} / {totalScenes} · 预计 {scene.estimated_minutes || 3} 分钟</Text>
        </div>
      </div>

      <div className="classroom-canvas-body">
        {scene.scene_type === 'introduction' && <IntroductionScene scene={scene} />}
        {scene.scene_type === 'presentation' && <PresentationScene scene={scene} />}
        {scene.scene_type === 'whiteboard' && <WhiteboardScene scene={scene} />}
        {scene.scene_type === 'simulation' && <SimulationScene scene={scene} onActionsChange={onSimulationActionsChange} />}
        {scene.scene_type === 'discussion' && <DiscussionScene scene={scene} />}
        {scene.scene_type === 'quiz' && <QuizScene scene={scene} classroom={classroom} session={session} />}
        {scene.scene_type === 'code_demo' && <CodeDemoScene scene={scene} />}
        {scene.scene_type === 'summary' && <SummaryScene scene={scene} />}
      </div>
    </Card>
  )
}
