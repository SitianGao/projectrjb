import { useMemo, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import * as echarts from 'echarts'
import { Empty, Spin } from 'antd'
import { useTheme } from '../contexts/ThemeContext'
import {
  getStageStatus,
  computeStageDays,
  computeStageDifficulty,
  DIFFICULTY_LABELS,
  getStageStatusColors,
} from '../utils/stageUtils'

/**
 * 阶段折线图组件
 *
 * 将学习路径的阶段可视化为折线图，每个拐点代表一个阶段。
 * 点击拐点可跳转到该阶段的资源详情页。
 *
 * Props:
 *   stages       — 阶段数组，每项含 stage_id, title, description, objectives, topics, tasks
 *   currentStage — 当前阶段编号（1-based）
 *   onStageClick — 点击拐点回调 (stage, index) => void
 *   height       — 图表高度（默认 400）
 *   loading      — 是否加载中
 */
export default function StageLineChart({
  stages = [],
  currentStage = 1,
  onStageClick,
  height = 400,
  loading = false,
}) {
  const { resolved: themeMode } = useTheme()
  const isDark = themeMode === 'dark'

  const textColor = isDark ? '#bbb' : '#666'
  const axisLineColor = isDark ? '#333' : '#e8e8e8'
  const gridLineColor = isDark ? '#222' : '#f0f0f0'

  const handleClick = useCallback(
    (params) => {
      const idx = params.dataIndex
      if (idx == null || !stages[idx]) return
      const stage = stages[idx]
      // 锁定状态不可点击
      if (getStageStatus(stage, currentStage) === 'locked') return
      onStageClick?.(stage, idx)
    },
    [stages, currentStage, onStageClick],
  )

  const option = useMemo(() => {
    if (!stages.length) return null

    // 根据当前阶段计算每个阶段的状态，并为每个数据点配置样式
    const xData = stages.map((s) => {
      const title = s.title || `阶段${s.stage_id}`
      return title.length > 8 ? title.slice(0, 7) + '…' : title
    })

    const yData = stages.map((s) => computeStageDifficulty(s))

    // 标记区域：已完成(绿)、当前(蓝)、锁定(灰)
    const markAreas = []
    const currentIdx = stages.findIndex((s) => Number(s.stage_id) === currentStage)
    if (currentIdx > 0) {
      markAreas.push([
        { xAxis: 0, itemStyle: { color: 'rgba(82,196,26,0.04)' } },
        { xAxis: currentIdx - 1 },
      ])
    }

    const seriesData = stages.map((s, idx) => {
      const status = getStageStatus(s, currentStage)
      const colors = getStageStatusColors(isDark)[status]
      return {
        value: yData[idx],
        symbol: 'circle',
        symbolSize: status === 'in_progress' ? 22 : 14,
        itemStyle: {
          color: status === 'locked' ? 'transparent' : colors.fill,
          borderColor: colors.border,
          borderWidth: 2.5,
          shadowBlur: status === 'in_progress' ? 12 : 0,
          shadowColor: colors.glow,
        },
        label: {
          show: true,
          position: 'top',
          distance: 14,
          fontSize: 11,
          color: status === 'locked' ? (isDark ? '#555' : '#bfbfbf') : (isDark ? '#ddd' : '#333'),
          fontWeight: status === 'in_progress' ? 700 : 400,
          formatter: xData[idx],
        },
        emphasis: {
          scale: 1.6,
          itemStyle: {
            shadowBlur: 20,
            shadowColor: colors.glow,
          },
        },
      }
    })

    const areaColor1 = isDark
      ? 'rgba(139,92,246,0.12)'
      : 'rgba(139,92,246,0.1)'
    const areaColor2 = 'rgba(139,92,246,0.0)'

    return {
      tooltip: {
        trigger: 'item',
        backgroundColor: isDark ? '#1f1f1f' : '#fff',
        borderColor: isDark ? '#333' : '#e8e8e8',
        textStyle: { fontSize: 13, color: isDark ? '#ddd' : '#333' },
        formatter(params) {
          const idx = params.dataIndex
          const s = stages[idx]
          if (!s) return ''
          const status = getStageStatus(s, currentStage)
          const statusLabel =
            status === 'completed'
              ? '✅ 已完成'
              : status === 'in_progress'
                ? '🔵 进行中'
                : '🔒 未解锁'
          const days = computeStageDays(s)
          const difficulty = DIFFICULTY_LABELS[computeStageDifficulty(s)] || '--'
          const topics = (s.topics || []).join('、') || '--'
          const objectives = (s.objectives || []).slice(0, 2).join('<br/>')
          const taskCount = (s.tasks || []).length

          return `
            <div style="max-width:260px">
              <strong style="font-size:14px">${s.title || `阶段${s.stage_id}`}</strong>
              <span style="margin-left:6px;font-size:12px">${statusLabel}</span>
              ${s.description ? `<br/><span style="color:#888;font-size:12px">${s.description.slice(0, 80)}${s.description.length > 80 ? '…' : ''}</span>` : ''}
              <br/><span style="color:#888;font-size:11px">
                主题：${topics} &nbsp;|&nbsp; 难度：${difficulty}<br/>
                任务：${taskCount} 项 &nbsp;|&nbsp; 预计 ${days} 天
                ${objectives ? '<br/>目标：' + objectives : ''}
              </span>
              ${status !== 'locked' ? '<br/><span style="color:#8b5cf6;font-size:11px">💡 点击查看该阶段学习资源</span>' : ''}
            </div>
          `
        },
      },
      grid: {
        left: 50,
        right: 40,
        top: 60,
        bottom: 40,
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLine: { lineStyle: { color: axisLineColor } },
        axisTick: { show: false },
        axisLabel: {
          fontSize: 11,
          color: textColor,
          interval: 0,
          rotate: stages.length > 6 ? 30 : 0,
        },
      },
      yAxis: {
        type: 'value',
        name: '难度',
        nameTextStyle: { fontSize: 11, color: textColor },
        min: 0,
        max: 5,
        interval: 1,
        axisLabel: {
          fontSize: 11,
          color: textColor,
          formatter(v) {
            return DIFFICULTY_LABELS[v] || ''
          },
        },
        splitLine: { lineStyle: { color: gridLineColor, type: 'dashed' } },
      },
      series: [
        {
          type: 'line',
          data: seriesData,
          smooth: 0.3,
          lineStyle: {
            color: '#8b5cf6',
            width: 3,
            shadowBlur: 8,
            shadowColor: 'rgba(139,92,246,0.3)',
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: areaColor1 },
              { offset: 1, color: areaColor2 },
            ]),
          },
          emphasis: {
            focus: 'series',
          },
          markArea: markAreas.length
            ? {
                silent: true,
                data: markAreas,
              }
            : undefined,
        },
      ],
    }
  }, [stages, currentStage, isDark, textColor, axisLineColor, gridLineColor])

  const onEvents = useMemo(() => ({ click: handleClick }), [handleClick])

  if (loading) {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Spin tip="加载课程数据..." />
      </div>
    )
  }

  if (!stages.length) {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Empty description="暂无课程阶段" />
      </div>
    )
  }

  return (
    <ReactECharts
      option={option}
      style={{ height, width: '100%' }}
      opts={{ renderer: 'canvas' }}
      onEvents={onEvents}
      notMerge
      lazyUpdate
    />
  )
}
