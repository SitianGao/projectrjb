import { Typography } from 'antd'
import LearningRateSimulation from './LearningRateSimulation'

const { Paragraph } = Typography

export default function SimulationScene({ scene, onActionsChange }) {
  return (
    <div>
      <Paragraph>{scene.content?.prompt}</Paragraph>
      <LearningRateSimulation onActionsChange={onActionsChange} />
    </div>
  )
}
