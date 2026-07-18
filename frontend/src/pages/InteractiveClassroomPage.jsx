import { useCallback, useMemo, useState } from 'react'
import { Button, Result, Skeleton, message } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import ClassroomContextHeader from '../components/classroom/ClassroomContextHeader'
import ClassroomSceneSidebar from '../components/classroom/ClassroomSceneSidebar'
import InteractiveClassroomCanvas from '../components/classroom/InteractiveClassroomCanvas'
import ClassroomTutorPanel from '../components/classroom/ClassroomTutorPanel'
import ClassroomActionFooter from '../components/classroom/ClassroomActionFooter'
import ClassroomProgressCard from '../components/classroom/ClassroomProgressCard'
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

  const selectScene = useCallback((sceneId) => {
    const index = sceneById.get(sceneId)
    if (index == null) return
    const status = progress.sceneStatus(scenes[index], index, safeCurrentIndex)
    if (status === 'locked') return
    setCurrentIndex(index)
  }, [progress, safeCurrentIndex, sceneById, scenes])

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
            <Button key="reload" type="primary" onClick={reload}>重新加载</Button>,
            <Button key="path" onClick={() => navigate(`/course/${courseId}/path`)}>返回学习路径</Button>,
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

  return (
    <div className="interactive-classroom-page">
      <div className="interactive-classroom-shell">
        <ClassroomContextHeader
          classroom={classroom}
          currentIndex={safeCurrentIndex}
          onBack={() => navigate(`/course/${courseId}/path`)}
        />
        <ClassroomProgressCard progress={progress} session={session} />
        <div className="interactive-classroom-layout">
          <ClassroomSceneSidebar
            scenes={scenes}
            currentIndex={safeCurrentIndex}
            progress={progress}
            getStatus={progress.sceneStatus}
            onSelect={selectScene}
          />
          <div className="classroom-main-column">
            <InteractiveClassroomCanvas
              scene={currentScene}
              sceneIndex={safeCurrentIndex}
              totalScenes={scenes.length}
              classroom={classroom}
              session={session}
              onSimulationActionsChange={setSimulationActions}
            />
            <ClassroomActionFooter
              isFirst={isFirst}
              isLast={isLast}
              completing={completionApi.loading}
              onPrev={() => setCurrentIndex((value) => Math.max(value - 1, 0))}
              onCompleteScene={completeCurrentScene}
              onCompleteClassroom={completeClassroom}
            />
          </div>
          <ClassroomTutorPanel
            currentScene={currentScene}
            messages={tutor.messages}
            loading={tutor.loading}
            onAsk={tutor.ask}
            intervention={intervention}
          />
        </div>
      </div>
    </div>
  )
}
