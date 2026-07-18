import { useMemo, useState } from 'react'

export function useClassroomSimulation() {
  const [learningRate, setLearningRate] = useState(0.1)
  const [running, setRunning] = useState(false)
  const [epoch, setEpoch] = useState(0)
  const [points, setPoints] = useState([{ epoch: 0, loss: 4 }])
  const [actions, setActions] = useState([])

  const convergence = useMemo(() => {
    if (learningRate <= 0.01) return '收敛速度很慢'
    if (learningRate <= 0.1) return '稳定下降并逐渐收敛'
    return learningRate >= 1 ? '损失值震荡或发散' : '下降较快但需要观察'
  }, [learningRate])

  const step = () => {
    setEpoch((prev) => prev + 1)
    setPoints((prev) => {
      const last = prev[prev.length - 1]?.loss ?? 4
      const nextLoss = learningRate >= 1
        ? Math.min(12, Math.abs(last * (1 + learningRate * 0.35) - 1.2))
        : Math.max(0.04, last * (1 - Math.min(0.75, learningRate * 4)))
      return [...prev, { epoch: prev.length, loss: Number(nextLoss.toFixed(3)) }].slice(-24)
    })
  }

  const chooseRate = (value) => {
    setLearningRate(value)
    setActions((prev) => [...prev, {
      action: 'set_learning_rate',
      value,
      operation_timestamp: new Date().toISOString(),
    }])
  }

  const reset = () => {
    setRunning(false)
    setEpoch(0)
    setPoints([{ epoch: 0, loss: 4 }])
  }

  return { learningRate, chooseRate, running, setRunning, epoch, points, step, reset, convergence, actions }
}
