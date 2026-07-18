import { useCallback, useMemo, useState } from 'react'
import { updateClassroomScene } from '../services/classroomSessionService'

export function useClassroomProgress(classroom, session) {
  const [completedSceneIds, setCompletedSceneIds] = useState(new Set())
  const total = classroom?.scenes?.length || 0
  const completed = completedSceneIds.size
  const percent = total ? Math.round((completed / total) * 100) : 0

  const sceneStatus = useCallback((scene, index, currentIndex) => {
    if (completedSceneIds.has(scene.scene_id)) return 'completed'
    if (index === currentIndex) return 'in_progress'
    if (index > currentIndex + 1) return 'locked'
    return 'not_started'
  }, [completedSceneIds])

  const completeScene = useCallback(async (scene, interactions = []) => {
    if (!classroom?.classroom_id || !session?.session_id || !scene?.scene_id) return
    await updateClassroomScene(classroom.classroom_id, session.session_id, scene.scene_id, {
      status: 'completed',
      progress: 1,
      interactions,
    })
    setCompletedSceneIds((prev) => new Set([...prev, scene.scene_id]))
  }, [classroom?.classroom_id, session?.session_id])

  return useMemo(() => ({
    completed,
    total,
    percent,
    completedSceneIds,
    sceneStatus,
    completeScene,
  }), [completed, total, percent, completedSceneIds, sceneStatus, completeScene])
}
