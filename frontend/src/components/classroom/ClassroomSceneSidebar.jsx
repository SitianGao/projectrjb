import { Card, Progress, Typography } from 'antd'
import ClassroomSceneItem from './ClassroomSceneItem'

const { Text } = Typography

export default function ClassroomSceneSidebar({ scenes, currentIndex, progress, getStatus, onSelect }) {
  return (
    <Card className="classroom-sidebar" title="课堂场景目录">
      <div className="classroom-scene-list">
        {scenes.map((scene, index) => (
          <ClassroomSceneItem
            key={scene.scene_id}
            scene={scene}
            active={index === currentIndex}
            status={getStatus(scene, index, currentIndex)}
            onClick={() => onSelect(scene.scene_id)}
          />
        ))}
      </div>
      <div className="classroom-progress-bottom">
        <Text strong>课堂进度</Text>
        <Text>{progress.completed} / {progress.total}</Text>
        <Progress percent={progress.percent} strokeColor="#6C5CE7" />
      </div>
    </Card>
  )
}
