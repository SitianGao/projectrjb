import {
  RobotOutlined,
  BookOutlined,
  FireOutlined,
  RiseOutlined,
  CheckCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons'

// Simple CSS radar chart using polygon
function RadarChart() {
  const points = [
    [50, 8], [88, 30], [78, 72], [50, 88], [22, 72], [12, 30],
  ]
  const data = [
    [50, 22], [74, 34], [66, 60], [50, 70], [34, 60], [28, 36],
  ]
  const hexToPoints = (pts) => pts.map(([x, y]) => `${x},${y}`).join(' ')

  return (
    <div className="lp-radar">
      <svg viewBox="0 0 100 100" className="lp-radar__svg">
        {/* Grid rings */}
        {[0.33, 0.66, 1].map((scale, i) => {
          const ring = points.map(([x, y]) => [
            50 + (x - 50) * scale,
            50 + (y - 50) * scale,
          ])
          return <polygon key={i} points={hexToPoints(ring)} className="lp-radar__ring" />
        })}
        {/* Data polygon */}
        <polygon points={hexToPoints(data)} className="lp-radar__data" />
        {/* Axis lines */}
        {points.map(([x, y], i) => (
          <line key={i} x1="50" y1="50" x2={x} y2={y} className="lp-radar__axis" />
        ))}
      </svg>
      <div className="lp-radar__labels">
        <span style={{ top: '-2px', left: '50%', transform: 'translateX(-50%)' }}>知识基础</span>
        <span style={{ top: '22%', right: '-2px' }}>学习目标</span>
        <span style={{ top: '65%', right: '-2px' }}>认知风格</span>
        <span style={{ bottom: '-2px', left: '50%', transform: 'translateX(-50%)' }}>薄弱点</span>
        <span style={{ top: '65%', left: '-2px' }}>学习历史</span>
        <span style={{ top: '22%', left: '-2px' }}>兴趣方向</span>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, color }) {
  return (
    <div className="lp-preview-stat">
      <div className="lp-preview-stat__icon" style={{ color }}>{icon}</div>
      <div className="lp-preview-stat__info">
        <span className="lp-preview-stat__value">{value}</span>
        <span className="lp-preview-stat__label">{label}</span>
      </div>
    </div>
  )
}

function TaskItem({ text, status }) {
  return (
    <div className="lp-preview-task">
      <CheckCircleOutlined style={{ color: status === 'done' ? '#2ac99a' : '#d0d5dd', fontSize: 13 }} />
      <span className={status === 'done' ? 'lp-preview-task--done' : ''}>{text}</span>
    </div>
  )
}

function AgentStatus({ name, color, status }) {
  return (
    <div className="lp-preview-agent">
      <span className="lp-preview-agent__dot" style={{ background: color }} />
      <span className="lp-preview-agent__name">{name}</span>
      <span className="lp-preview-agent__status">{status}</span>
    </div>
  )
}

export default function ProductPreview() {
  return (
    <div className="lp-preview-wrapper">
      <div className="lp-preview-float lp-preview-float--1">
        <RobotOutlined style={{ color: '#6256e8', marginRight: 6 }} />
        <span>AI 导师：发现新的学习建议</span>
      </div>
      <div className="lp-preview-float lp-preview-float--2">
        <FireOutlined style={{ color: '#fa8c16', marginRight: 6 }} />
        <span>连续学习 7 天</span>
      </div>
      <div className="lp-preview-float lp-preview-float--3">
        <SyncOutlined style={{ color: '#2ac99a', marginRight: 6 }} />
        <span>五个 Agent 已协同完成规划</span>
      </div>

      <div className="lp-preview-window">
        <div className="lp-preview-window__bar">
          <span className="lp-preview-dot lp-preview-dot--red" />
          <span className="lp-preview-dot lp-preview-dot--yellow" />
          <span className="lp-preview-dot lp-preview-dot--green" />
          <span className="lp-preview-window__title">EduAgent — 学习概览</span>
        </div>

        <div className="lp-preview-window__body">
          <div className="lp-preview-stats">
            <StatCard icon={<RiseOutlined />} label="学习进度" value="68%" color="#6256e8" />
            <StatCard icon={<BookOutlined />} label="知识掌握度" value="74%" color="#258cf4" />
            <StatCard icon={<FireOutlined />} label="连续学习" value="7 天" color="#fa8c16" />
          </div>

          <div className="lp-preview-main">
            <div className="lp-preview-main__left">
              <RadarChart />
            </div>
            <div className="lp-preview-main__right">
              <div className="lp-preview-section">
                <div className="lp-preview-section__title">今日学习任务</div>
                <TaskItem text="第三章 线性回归 — 阅读讲义" status="done" />
                <TaskItem text="完成课后练习题（共 8 题）" status="done" />
                <TaskItem text="梯度下降算法笔记整理" status="pending" />
              </div>
              <div className="lp-preview-section">
                <div className="lp-preview-section__title">Agent 运行状态</div>
                <AgentStatus name="ProfileAgent" color="#6256e8" status="就绪" />
                <AgentStatus name="PlannerAgent" color="#258cf4" status="运行中" />
                <AgentStatus name="EvaluateAgent" color="#2ac99a" status="就绪" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
