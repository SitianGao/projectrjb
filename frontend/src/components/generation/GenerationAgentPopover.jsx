import { useState } from 'react'
import { Button, Popover, Tag } from 'antd'
import { TeamOutlined, CheckCircleFilled, SyncOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { AGENTS } from './generationAgents'

function statusIcon(status) {
  if (status === 'active') return <SyncOutlined spin style={{ color: '#6C5CE7' }} />
  if (status === 'completed') return <CheckCircleFilled style={{ color: '#22C55E' }} />
  return <ClockCircleOutlined style={{ color: '#D1D5DB' }} />
}

function statusLabel(status) {
  if (status === 'active') return '工作中'
  if (status === 'completed') return '已完成'
  return '等待中'
}

export default function GenerationAgentPopover({ activeStepIndex }) {
  const [open, setOpen] = useState(false)

  const agentsWithStatus = AGENTS.map((a, i) => ({
    ...a,
    currentStatus: i < activeStepIndex ? 'completed' : i === activeStepIndex ? 'active' : 'idle',
  }))

  const content = (
    <div style={{ width: 280, padding: '4px 0' }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 12 }}>
        多智能体协同工作
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {agentsWithStatus.map((agent) => (
          <div
            key={agent.name}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 12px',
              borderRadius: 10,
              background: agent.currentStatus === 'active' ? 'rgba(108,92,231,0.04)' : 'transparent',
              border: agent.currentStatus === 'active'
                ? '1px solid rgba(108,92,231,0.12)'
                : '1px solid transparent',
            }}
          >
            <div
              style={{
                width: 32, height: 32, borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 16, background: agent.bg, flexShrink: 0,
              }}
            >
              {agent.icon}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>
                {agent.name}
              </div>
              <div style={{ fontSize: 11, color: '#9CA3AF' }}>{agent.role}</div>
            </div>
            <div style={{ flexShrink: 0 }}>
              {statusIcon(agent.currentStatus)}
              <span style={{ fontSize: 11, color: '#9CA3AF', marginLeft: 4 }}>
                {statusLabel(agent.currentStatus)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )

  return (
    <div className="gen-view-roles">
      <Popover
        content={content}
        title={null}
        trigger="click"
        open={open}
        onOpenChange={setOpen}
        placement="topRight"
        overlayStyle={{ maxWidth: 320 }}
      >
        <Button
          icon={<TeamOutlined />}
          type="default"
          style={{
            borderRadius: 20,
            border: '1px solid rgba(108,92,231,0.2)',
            color: '#6C5CE7',
            fontWeight: 500,
            fontSize: 13,
            padding: '4px 18px',
            height: 36,
            background: 'rgba(255,255,255,0.7)',
            backdropFilter: 'blur(8px)',
          }}
        >
          查看角色
        </Button>
      </Popover>
    </div>
  )
}
