import { Button, Tooltip } from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  CheckCircleFilled,
  MinusCircleOutlined,
  LockOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'

function SceneStatusIcon({ status }) {
  if (status === 'completed') return <CheckCircleFilled style={{ color: '#22C55E', fontSize: 16 }} />
  if (status === 'locked') return <LockOutlined style={{ color: '#D1D5DB', fontSize: 16 }} />
  return <MinusCircleOutlined style={{ color: '#6C5CE7', fontSize: 16 }} />
}

export default function ClassroomTaskOutline({
  scenes,
  currentIndex,
  sceneStatusFn,
  onSelectScene,
  collapsed,
  onToggleCollapse,
  estimatedTimes,
}) {
  return (
    <div
      className="classroom-task-outline"
      style={{
        width: collapsed ? 40 : 220,
        flexShrink: 0,
        borderRight: '1px solid rgba(0,0,0,0.06)',
        background: 'rgba(255,255,255,0.85)',
        backdropFilter: 'blur(12px)',
        transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 30,
      }}
    >
      {/* Toggle header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          padding: collapsed ? '12px 0' : '12px 16px',
          borderBottom: '1px solid rgba(0,0,0,0.04)',
        }}
      >
        {!collapsed && (
          <span style={{ fontSize: 13, fontWeight: 700, color: '#374151' }}>任务目录</span>
        )}
        <Button
          type="text"
          size="small"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={onToggleCollapse}
          style={{ color: '#9CA3AF', fontSize: 16 }}
        />
      </div>

      {/* Scene list */}
      {!collapsed && (
        <div style={{ flex: 1, overflow: 'auto', padding: '8px 0' }}>
          {scenes.map((scene, i) => {
            const status = sceneStatusFn ? sceneStatusFn(scene, i, currentIndex) : 'locked'
            const isActive = i === currentIndex
            const time = estimatedTimes ? estimatedTimes[i] : null

            return (
              <div
                key={scene.scene_id || i}
                onClick={() => status !== 'locked' && onSelectScene(scene.scene_id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 16px',
                  margin: '2px 8px',
                  borderRadius: 10,
                  cursor: status === 'locked' ? 'not-allowed' : 'pointer',
                  background: isActive
                    ? 'rgba(108,92,231,0.06)'
                    : 'transparent',
                  border: isActive
                    ? '1px solid rgba(108,92,231,0.15)'
                    : '1px solid transparent',
                  transition: 'all 0.2s',
                  opacity: status === 'locked' ? 0.4 : 1,
                }}
                onMouseEnter={(e) => {
                  if (status !== 'locked' && !isActive) {
                    e.currentTarget.style.background = 'rgba(108,92,231,0.03)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent'
                  }
                }}
              >
                <SceneStatusIcon status={status} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: isActive ? 600 : 500,
                      color: isActive ? '#6C5CE7' : status === 'completed' ? '#374151' : '#6B7280',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {scene.title || `场景 ${i + 1}`}
                  </div>
                  {time && (
                    <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2, display: 'flex', alignItems: 'center', gap: 4 }}>
                      <ClockCircleOutlined style={{ fontSize: 10 }} />
                      {time}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Progress summary at bottom */}
      {!collapsed && (
        <div
          style={{
            padding: '12px 16px',
            borderTop: '1px solid rgba(0,0,0,0.04)',
            fontSize: 12,
            color: '#9CA3AF',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span>已完成</span>
            <span style={{ fontWeight: 600, color: '#6C5CE7' }}>
              {scenes.filter((_s, i) => i < currentIndex).length} / {scenes.length}
            </span>
          </div>
          <div
            style={{
              height: 4,
              borderRadius: 2,
              background: 'rgba(0,0,0,0.06)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                borderRadius: 2,
                width: `${((currentIndex + 1) / Math.max(scenes.length, 1)) * 100}%`,
                background: 'linear-gradient(90deg, #6C5CE7, #8B7CF7)',
                transition: 'width 0.5s ease',
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
