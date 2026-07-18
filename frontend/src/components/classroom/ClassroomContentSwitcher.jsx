import { Segmented } from 'antd'
import {
  PlaySquareOutlined,
  FileTextOutlined,
  BranchesOutlined,
  CodeOutlined,
  FormOutlined,
} from '@ant-design/icons'

const VIEW_OPTIONS = [
  { label: 'PPT', value: 'slide', icon: <PlaySquareOutlined /> },
  { label: '讲义', value: 'lecture', icon: <FileTextOutlined /> },
  { label: '思维导图', value: 'mindmap', icon: <BranchesOutlined /> },
  { label: '代码', value: 'code', icon: <CodeOutlined /> },
  { label: '测验', value: 'quiz', icon: <FormOutlined /> },
]

export default function ClassroomContentSwitcher({
  currentView,
  onChange,
  availableViews,
}) {
  const options = VIEW_OPTIONS.filter((opt) =>
    !availableViews || availableViews.includes(opt.value)
  )

  if (options.length <= 1) return null

  return (
    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'center' }}>
      <Segmented
        value={currentView}
        onChange={onChange}
        options={options.map((opt) => ({
          label: (
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              {opt.icon}
              <span>{opt.label}</span>
            </span>
          ),
          value: opt.value,
        }))}
        style={{
          background: 'rgba(108,92,231,0.06)',
          borderRadius: 12,
          padding: 4,
        }}
      />
    </div>
  )
}

/** Derives available views from scene type and content */
export function getAvailableViews(scene) {
  if (!scene) return ['slide']
  const views = ['slide']
  const type = scene.scene_type

  // Most scene types support lecture view
  if (['introduction', 'presentation', 'whiteboard', 'discussion', 'summary', 'code_demo'].includes(type)) {
    views.push('lecture')
  }

  // Mindmap if scene has structured content
  if (scene.content?.mindmap_data || (type !== 'quiz' && type !== 'simulation')) {
    views.push('mindmap')
  }

  // Code view for code_demo scenes or scenes with code snippets
  if (type === 'code_demo' || scene.content?.code_snippet) {
    views.push('code')
  }

  // Quiz view only for quiz scenes
  if (type === 'quiz' || scene.content?.questions) {
    views.push('quiz')
  }

  return views
}
