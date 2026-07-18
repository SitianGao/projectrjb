import { useMemo, useState } from 'react'

export function useClassroomScenes(classroom) {
  const scenes = useMemo(() => classroom?.scenes || [], [classroom])
  const [currentSceneId, setCurrentSceneId] = useState(null)
  const currentScene = scenes.find((scene) => scene.scene_id === (currentSceneId || scenes[0]?.scene_id)) || scenes[0]
  const currentIndex = scenes.findIndex((scene) => scene.scene_id === currentScene?.scene_id)
  return { scenes, currentScene, currentIndex, setCurrentSceneId }
}
