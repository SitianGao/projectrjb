import { CheckCircleOutlined, LockOutlined, PlayCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons'

const STATUS_LABEL = {
  completed: '已完成',
  in_progress: '学习中',
  not_started: '未开始',
  locked: '锁定',
  review_required: '需回看',
}

export default function ClassroomSceneItem({ scene, status, active, onClick }) {
  const Icon = status === 'completed'
    ? CheckCircleOutlined
    : status === 'locked'
      ? LockOutlined
      : status === 'review_required'
        ? ExclamationCircleOutlined
        : PlayCircleOutlined
  return (
    <button className={`classroom-scene-item is-${status}${active ? ' is-active' : ''}`} onClick={onClick} disabled={status === 'locked'} title={status === 'locked' ? '完成上一场景后解锁。' : scene.title}>
      <Icon />
      <span>
        <strong>{scene.order} {scene.title}</strong>
        <small>{scene.scene_type} · {scene.estimated_minutes} 分钟</small>
      </span>
      <em>{STATUS_LABEL[status]}</em>
    </button>
  )
}
