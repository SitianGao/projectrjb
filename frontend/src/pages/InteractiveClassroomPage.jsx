import { useCallback, useMemo, useState } from 'react'
import { Button, Result, Skeleton, message } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import ClassroomInfoBar from '../components/classroom/ClassroomInfoBar'
import ClassroomTaskOutline from '../components/classroom/ClassroomTaskOutline'
import ClassroomContentSwitcher, { getAvailableViews } from '../components/classroom/ClassroomContentSwitcher'
import ClassroomFloatingToolbar from '../components/classroom/ClassroomFloatingToolbar'
import ClassroomAITutorBar from '../components/classroom/ClassroomAITutorBar'
import ClassroomControlBar from '../components/classroom/ClassroomControlBar'
import ClassroomNotesDrawer from '../components/classroom/ClassroomNotesDrawer'
import ClassroomKnowledgeDrawer from '../components/classroom/ClassroomKnowledgeDrawer'
import ClassroomProgressDrawer from '../components/classroom/ClassroomProgressDrawer'
import InteractiveClassroomCanvas from '../components/classroom/InteractiveClassroomCanvas'
import ClassroomCompletionResult from '../components/classroom/ClassroomCompletionResult'
import { useInteractiveClassroom } from '../hooks/useInteractiveClassroom'
import { useClassroomSession } from '../hooks/useClassroomSession'
import { useClassroomProgress } from '../hooks/useClassroomProgress'
import { useClassroomTutor } from '../hooks/useClassroomTutor'
import { useTutorIntervention } from '../hooks/useTutorIntervention'
import { useCompleteClassroom } from '../hooks/useCompleteClassroom'
import './InteractiveClassroomPage.css'

export default function InteractiveClassroomPage() {
  const { courseId, classroomId } = useParams()

  return (
    <InteractiveClassroomTaskContent
      courseId={courseId}
      classroomId={classroomId}
    />
  )
}

export function InteractiveClassroomTaskContent({ courseId, classroomId }) {
  const navigate = useNavigate()
  const { classroom, loading, error, reload } = useInteractiveClassroom({ courseId, classroomId })
  const { session } = useClassroomSession(classroom?.classroom_id)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [simulationActions, setSimulationActions] = useState([])
  const [intervention, setIntervention] = useState(null)
  const [completion, setCompletion] = useState(null)

  // New UI state
  const [contentView, setContentView] = useState('slide')
  const [outlineCollapsed, setOutlineCollapsed] = useState(false)
  const [focusMode, setFocusMode] = useState(false)
  const [tutorExpanded, setTutorExpanded] = useState(false)
  const [activePanel, setActivePanel] = useState(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const scenes = classroom?.scenes || []
  const currentScene = scenes[currentIndex] || null
  const progress = useClassroomProgress(classroom, session)
  const tutor = useClassroomTutor(classroom, session, currentScene)
  const interventionApi = useTutorIntervention(classroom, session)
  const completionApi = useCompleteClassroom(classroom, session)

  const safeCurrentIndex = Math.min(currentIndex, Math.max(scenes.length - 1, 0))
  const isFirst = safeCurrentIndex <= 0
  const isLast = scenes.length > 0 && safeCurrentIndex >= scenes.length - 1

  const sceneById = useMemo(() => {
    const map = new Map()
    scenes.forEach((scene, index) => map.set(scene.scene_id, index))
    return map
  }, [scenes])

  const availableViews = useMemo(
    () => getAvailableViews(currentScene),
    [currentScene]
  )

  // Sync contentView when available views change
  useMemo(() => {
    if (!availableViews.includes(contentView)) {
      setContentView(availableViews[0] || 'slide')
    }
  }, [availableViews, contentView])

  const selectScene = useCallback(
    (sceneId) => {
      const index = sceneById.get(sceneId)
      if (index == null) return
      const status = progress.sceneStatus(scenes[index], index, safeCurrentIndex)
      if (status === 'locked') return
      setCurrentIndex(index)
      setContentView('slide')
    },
    [progress, safeCurrentIndex, sceneById, scenes]
  )

  const completeCurrentScene = useCallback(async () => {
    if (!currentScene) return
    await progress.completeScene(currentScene, simulationActions)
    if (currentScene.scene_type === 'simulation') {
      const result = await interventionApi.check(currentScene.scene_id, simulationActions)
      setIntervention(result)
      if (result?.should_intervene || result?.need_intervention) {
        await tutor.ask('我刚才的学习率选择哪里有问题？', { action: 'auto_intervention' })
        message.warning('AI 导师检测到学习率可能过大，已给出提醒。')
        return
      }
    }
    setCurrentIndex((value) => Math.min(value + 1, scenes.length - 1))
  }, [currentScene, interventionApi, progress, scenes.length, simulationActions, tutor])

  const completeClassroom = useCallback(async () => {
    if (!currentScene) return
    await progress.completeScene(currentScene, simulationActions)
    const result = await completionApi.complete()
    setCompletion(result)
    message.success('互动课堂已完成，学习画像已更新。')
  }, [completionApi, currentScene, progress, simulationActions])

  const handlePanelChange = (panel) => {
    setActivePanel(panel)
    if (panel === 'tutor') {
      setTutorExpanded(true)
    }
  }

  // Scene status function for the outline
  const sceneStatusFn = useCallback(
    (scene, index, _current) => {
      if (index < safeCurrentIndex) return 'completed'
      if (index === safeCurrentIndex) return 'active'
      // Simplified: all future scenes are unlocked (locked would require progress tracking)
      return 'unlocked'
    },
    [safeCurrentIndex]
  )

  const isQuizTask = currentScene?.scene_type === 'quiz'

  if (loading) {
    return (
      <div className="interactive-classroom-page">
        <Skeleton active paragraph={{ rows: 8 }} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="interactive-classroom-page">
        <Result
          status="warning"
          title="互动课堂暂时不可用"
          subTitle={error.message || '请稍后重试'}
          extra={[
            <Button key="reload" type="primary" onClick={reload}>
              重新加载
            </Button>,
            <Button key="path" onClick={() => navigate(`/course/${courseId}/path`)}>
              返回学习路径
            </Button>,
          ]}
        />
      </div>
    )
  }

  if (completion) {
    return (
      <div className="interactive-classroom-page">
        <ClassroomCompletionResult courseId={courseId} result={completion} />
      </div>
    )
  }

  // ═══════════════════════════════════════════════════════════
  //  NEW IMMERSIVE CLASSROOM LAYOUT
  // ═══════════════════════════════════════════════════════════

  return (
    <div
      className="interactive-classroom-page"
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        background: 'linear-gradient(160deg, #F6F7FB 0%, #EDE9FE 40%, #F6F7FB 100%)',
      }}
    >
      {/* ═══ 1) Top Info Bar ═══ */}
      <ClassroomInfoBar
        classroom={classroom}
        currentIndex={safeCurrentIndex}
        totalScenes={scenes.length}
        onBack={() => navigate(`/course/${courseId}/path`)}
        focusMode={focusMode}
        onToggleFocus={() => setFocusMode(!focusMode)}
        isFullscreen={isFullscreen}
        onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
      />

      {/* ═══ 2) Main Body: Outline + Stage ═══ */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0, position: 'relative' }}>
        {/* Left: Task Outline (collapsible) */}
        {!focusMode && (
          <ClassroomTaskOutline
            scenes={scenes}
            currentIndex={safeCurrentIndex}
            sceneStatusFn={sceneStatusFn}
            onSelectScene={selectScene}
            collapsed={outlineCollapsed}
            onToggleCollapse={() => setOutlineCollapsed(!outlineCollapsed)}
            estimatedTimes={scenes.map(() => {
              const types = { introduction: '5min', presentation: '12min', whiteboard: '8min', simulation: '15min', discussion: '10min', quiz: '8min', code_demo: '10min', summary: '5min' }
              return types[Math.floor(Math.random() * 8)] || '10min'
            })}
          />
        )}

        {/* Center: Main Stage */}
        <div
          style={{
            flex: 1,
            minWidth: 0,
            display: 'flex',
            flexDirection: 'column',
            padding: focusMode ? '0' : '20px',
            overflow: 'auto',
          }}
        >
          {/* Content Switcher */}
          {!focusMode && (
            <ClassroomContentSwitcher
              currentView={contentView}
              onChange={setContentView}
              availableViews={availableViews}
            />
          )}

          {/* Stage Card */}
          <div
            style={{
              flex: 1,
              minHeight: 0,
              borderRadius: focusMode ? 0 : 16,
              border: focusMode ? 'none' : '1px solid rgba(0,0,0,0.06)',
              boxShadow: focusMode ? 'none' : '0 8px 32px rgba(0,0,0,0.04)',
              background: '#fff',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <InteractiveClassroomCanvas
              scene={currentScene}
              sceneIndex={safeCurrentIndex}
              totalScenes={scenes.length}
              classroom={classroom}
              session={session}
              contentView={contentView}
              onSimulationActionsChange={setSimulationActions}
            />
          </div>
        </div>
      </div>

      {/* ═══ 3) Bottom AI Tutor Bar ═══ */}
      {!focusMode && (
        <ClassroomAITutorBar
          currentScene={currentScene}
          messages={tutor.messages}
          loading={tutor.loading}
          onAsk={tutor.ask}
          intervention={intervention}
          expanded={tutorExpanded}
          onToggleExpand={() => setTutorExpanded(!tutorExpanded)}
        />
      )}

      {/* ═══ 4) Bottom Control Bar ═══ */}
      <ClassroomControlBar
        isFirst={isFirst}
        isLast={isLast}
        completing={completionApi.loading}
        onPrev={() => setCurrentIndex((v) => Math.max(v - 1, 0))}
        onNext={completeCurrentScene}
        onComplete={completeClassroom}
        onMarkDifficult={() => {
          message.success('已标记为困难')
        }}
        onAddToWrongBook={() => {
          message.success('已加入错题本')
        }}
        onViewResources={() => {
          navigate(`/course/${courseId}/stage/${classroom?.stage_id || 'current'}`)
        }}
        isQuizTask={isQuizTask}
      />

      {/* ═══ Right Floating Toolbar ═══ */}
      {!focusMode && (
        <ClassroomFloatingToolbar
          activePanel={activePanel}
          onPanelChange={handlePanelChange}
        />
      )}

      {/* ═══ Drawers ═══ */}
      <ClassroomNotesDrawer
        open={activePanel === 'notes'}
        onClose={() => setActivePanel(null)}
        sceneId={currentScene?.scene_id}
        sceneTitle={currentScene?.title}
      />

      <ClassroomKnowledgeDrawer
        open={activePanel === 'knowledge'}
        onClose={() => setActivePanel(null)}
        currentScene={currentScene}
      />

      <ClassroomProgressDrawer
        open={activePanel === 'progress'}
        onClose={() => setActivePanel(null)}
        progress={progress}
        session={session}
        scenes={scenes}
        currentIndex={safeCurrentIndex}
      />
    </div>
  )
}
