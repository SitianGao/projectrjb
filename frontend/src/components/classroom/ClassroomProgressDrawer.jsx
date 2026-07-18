import { Drawer, Progress, Statistic, Typography, Row, Col } from 'antd'
import {
  BarChartOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
} from '@ant-design/icons'

const { Text } = Typography

export default function ClassroomProgressDrawer({ open, onClose, progress, session, scenes, currentIndex }) {
  const completedCount = scenes ? scenes.filter((_s, i) => i < currentIndex).length : 0
  const totalScenes = scenes?.length || 0
  const percent = totalScenes > 0 ? Math.round((completedCount / totalScenes) * 100) : 0

  // Mock stats (would come from real session data)
  const durationMinutes = session?.duration_minutes || Math.floor(Math.random() * 20 + 10)
  const questionsAsked = session?.tutor_questions || Math.floor(Math.random() * 5 + 1)

  return (
    <Drawer
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <BarChartOutlined style={{ color: '#6C5CE7' }} />
          <span>学习状态</span>
        </div>
      }
      placement="right"
      open={open}
      onClose={onClose}
      width={320}
      styles={{
        body: { padding: '20px 24px' },
        header: { borderBottom: '1px solid rgba(0,0,0,0.06)' },
      }}
      mask={false}
    >
      {/* Overall progress */}
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <Progress
          type="circle"
          percent={percent}
          size={120}
          strokeColor={{ from: '#6C5CE7', to: '#8B7CF7' }}
          format={() => (
            <span>
              <span style={{ fontSize: 28, fontWeight: 700, color: '#6C5CE7' }}>{percent}</span>
              <span style={{ fontSize: 14, color: '#9CA3AF' }}>%</span>
            </span>
          )}
        />
        <div style={{ marginTop: 12, fontSize: 13, color: '#6B7280' }}>
          课堂进度
        </div>
      </div>

      {/* Stats row */}
      <Row gutter={[12, 12]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <div
            style={{
              padding: '14px 12px',
              borderRadius: 12,
              background: 'rgba(108,92,231,0.04)',
              border: '1px solid rgba(108,92,231,0.08)',
              textAlign: 'center',
            }}
          >
            <CheckCircleOutlined style={{ fontSize: 20, color: '#22C55E', marginBottom: 6 }} />
            <div style={{ fontSize: 20, fontWeight: 700, color: '#111827' }}>
              {completedCount}/{totalScenes}
            </div>
            <div style={{ fontSize: 11, color: '#9CA3AF' }}>完成任务</div>
          </div>
        </Col>
        <Col span={12}>
          <div
            style={{
              padding: '14px 12px',
              borderRadius: 12,
              background: 'rgba(59,130,246,0.04)',
              border: '1px solid rgba(59,130,246,0.08)',
              textAlign: 'center',
            }}
          >
            <ClockCircleOutlined style={{ fontSize: 20, color: '#3B82F6', marginBottom: 6 }} />
            <div style={{ fontSize: 20, fontWeight: 700, color: '#111827' }}>
              {durationMinutes}min
            </div>
            <div style={{ fontSize: 11, color: '#9CA3AF' }}>学习时长</div>
          </div>
        </Col>
      </Row>

      {/* Additional stats */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderRadius: 10,
            background: 'rgba(0,0,0,0.02)',
            border: '1px solid rgba(0,0,0,0.04)',
          }}
        >
          <Text style={{ fontSize: 13, color: '#6B7280' }}>
            <TrophyOutlined style={{ marginRight: 8, color: '#F59E0B' }} />
            AI 提问次数
          </Text>
          <Text strong style={{ fontSize: 13, color: '#111827' }}>{questionsAsked} 次</Text>
        </div>

        {session?.quiz_score !== undefined && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '12px 16px',
              borderRadius: 10,
              background: 'rgba(0,0,0,0.02)',
              border: '1px solid rgba(0,0,0,0.04)',
            }}
          >
            <Text style={{ fontSize: 13, color: '#6B7280' }}>
              <TrophyOutlined style={{ marginRight: 8, color: '#22C55E' }} />
              即时测验
            </Text>
            <Text strong style={{ fontSize: 13, color: '#22C55E' }}>{session.quiz_score} 分</Text>
          </div>
        )}
      </div>
    </Drawer>
  )
}
