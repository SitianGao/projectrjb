import { useEffect } from 'react'
import { Button, Segmented, Space, Statistic, Typography } from 'antd'
import { PauseCircleOutlined, PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import { useClassroomSimulation } from '../../hooks/useClassroomSimulation'

const { Text } = Typography

export default function LearningRateSimulation({ onActionsChange }) {
  const sim = useClassroomSimulation()

  useEffect(() => {
    if (!sim.running) return
    const timer = window.setInterval(sim.step, 700)
    return () => window.clearInterval(timer)
  }, [sim])

  useEffect(() => {
    onActionsChange?.(sim.actions)
  }, [onActionsChange, sim.actions])

  const maxLoss = Math.max(...sim.points.map((p) => p.loss), 1)
  return (
    <div className="lr-simulation">
      <Segmented
        value={sim.learningRate}
        onChange={sim.chooseRate}
        options={[0.001, 0.01, 0.1, 1.0, 2.0].map((value) => ({ value, label: value }))}
      />
      <div className="loss-chart">
        {sim.points.map((point) => (
          <span key={point.epoch} style={{ height: `${Math.max(8, point.loss / maxLoss * 100)}%` }} title={`epoch ${point.epoch}: ${point.loss}`} />
        ))}
      </div>
      <Space wrap>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => sim.setRunning(true)}>开始训练</Button>
        <Button icon={<PauseCircleOutlined />} onClick={() => sim.setRunning(false)}>暂停训练</Button>
        <Button icon={<ReloadOutlined />} onClick={sim.reset}>重置</Button>
      </Space>
      <div className="simulation-stats">
        <Statistic title="学习率" value={sim.learningRate} />
        <Statistic title="训练轮次" value={sim.epoch} />
        <Statistic title="当前参数" value={(1 + Math.exp(-sim.epoch / 5)).toFixed(3)} />
      </div>
      <Text strong>{sim.convergence}</Text>
    </div>
  )
}
