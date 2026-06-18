import { useEffect } from 'react'
import { Typography } from 'antd'
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  FileTextOutlined,
  BulbOutlined,
  EditOutlined,
} from '@ant-design/icons'

const { Text } = Typography

const STEP_ICONS = {
  understand: <BulbOutlined />,
  prepare: <FileTextOutlined />,
  polish: <EditOutlined />,
}

/**
 * 生成进度组件
 *
 * 展示异步任务的实时进度：大号百分比 + 渐变色进度条 + 带图标的步骤指示器。
 *
 * @param {'idle'|'pending'|'running'|'completed'|'failed'} status
 * @param {number} percent - 0-100
 * @param {Array<{key:string, label:string, status:'wait'|'process'|'finish'|'error'}>} steps
 * @param {string} message - 当前状态描述
 * @param {string} error - 错误详情
 */
export default function ProgressBar({
  status = 'idle',
  percent = 0,
  steps = [],
  message = '',
  error = '',
}) {
  const isRunning = status === 'pending' || status === 'running'
  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'
  const displayPercent = isCompleted ? 100 : isFailed ? percent : percent

  // 注入 shimmer / pulse 动画（全局只注入一次）
  useEffect(() => {
    const id = 'pb-animations'
    if (document.getElementById(id)) return
    const style = document.createElement('style')
    style.id = id
    style.textContent = [
      '@keyframes pb-shimmer {',
      '  0%   { left: -100%; }',
      '  100% { left: 100%; }',
      '}',
      '@keyframes pb-pulse {',
      '  0%, 100% { box-shadow: 0 0 0 0 rgba(139,92,246,0.35); }',
      '  50%      { box-shadow: 0 0 0 8px rgba(139,92,246,0); }',
      '}',
    ].join('\n')
    document.head.appendChild(style)
  }, [])

  return (
    <div style={{ padding: '20px 0' }}>
      {/* ── 大号百分比 + 状态描述 ── */}
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <div
          style={{
            fontSize: 56,
            fontWeight: 800,
            lineHeight: 1.1,
            letterSpacing: '-0.02em',
            transition: 'color 0.4s',
            color: isFailed
              ? '#ff4d4f'
              : isCompleted
                ? '#22c55e'
                : '#7c3aed',
          }}
        >
          {isCompleted ? (
            <CheckCircleOutlined style={{ fontSize: 48 }} />
          ) : isFailed ? (
            <CloseCircleOutlined style={{ fontSize: 48 }} />
          ) : (
            <span>
              {displayPercent}
              <span style={{ fontSize: 28, fontWeight: 500 }}>%</span>
            </span>
          )}
        </div>
        {message && (
          <Text style={{ fontSize: 14, color: '#6b7280', marginTop: 6, display: 'block' }}>
            {isRunning && <LoadingOutlined style={{ marginRight: 6 }} spin />}
            {message}
          </Text>
        )}
      </div>

      {/* ── 渐变色进度条 ── */}
      <div style={{ marginBottom: 28, padding: '0 16px' }}>
        <div
          style={{
            height: 6,
            borderRadius: 3,
            background: '#f3f4f6',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <div
            style={{
              height: '100%',
              borderRadius: 3,
              width: `${Math.max(displayPercent, 2)}%`,
              background: isFailed
                ? '#ff4d4f'
                : isCompleted
                  ? 'linear-gradient(90deg, #22c55e, #4ade80)'
                  : 'linear-gradient(90deg, #7c3aed, #a78bfa, #c4b5fd)',
              backgroundSize: isRunning ? '200% 100%' : '100% 100%',
              transition: 'width 0.7s cubic-bezier(0.34, 1.56, 0.64, 1)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* shimmer 光效 */}
            {isRunning && (
              <span
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  width: '60%',
                  background:
                    'linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent)',
                  animation: 'pb-shimmer 1.6s ease-in-out infinite',
                }}
              />
            )}
          </div>
        </div>
      </div>

      {/* ── 步骤指示器 ── */}
      {steps.length > 0 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'flex-start',
            gap: 0,
          }}
        >
          {steps.map((step, i) => {
            const isDone = step.status === 'finish'
            const isCurrent = step.status === 'process'
            const icon =
              isCompleted || isDone
                ? <CheckCircleOutlined />
                : STEP_ICONS[step.key] || STEP_ICONS.understand

            return (
              <div
                key={step.key}
                style={{ display: 'flex', alignItems: 'flex-start' }}
              >
                {/* 单个步骤 */}
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    width: 72,
                  }}
                >
                  {/* 图标圆 */}
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 16,
                      transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                      background: isDone || isCompleted
                        ? 'linear-gradient(135deg, #dcfce7, #f0fdf4)'
                        : isCurrent
                          ? 'linear-gradient(135deg, #ede9fe, #f5f3ff)'
                          : '#f9fafb',
                      border: `2px solid ${
                        isDone || isCompleted
                          ? '#22c55e'
                          : isCurrent
                            ? '#7c3aed'
                            : '#e5e7eb'
                      }`,
                      color:
                        isDone || isCompleted
                          ? '#22c55e'
                          : isCurrent
                            ? '#7c3aed'
                            : '#d1d5db',
                      position: 'relative',
                    }}
                  >
                    {/* 当前步骤脉冲环 */}
                    {isCurrent && (
                      <span
                        style={{
                          position: 'absolute',
                          inset: -3,
                          borderRadius: '50%',
                          border: '2px solid rgba(124,58,237,0.25)',
                          animation: 'pb-pulse 2.2s ease-in-out infinite',
                        }}
                      />
                    )}
                    {icon}
                  </div>
                  {/* 步骤名 */}
                  <span
                    style={{
                      fontSize: 12,
                      marginTop: 8,
                      fontWeight: isCurrent ? 600 : 400,
                      color: isDone || isCompleted
                        ? '#22c55e'
                        : isCurrent
                          ? '#7c3aed'
                          : '#9ca3af',
                      whiteSpace: 'nowrap',
                      transition: 'color 0.3s',
                    }}
                  >
                    {step.label}
                  </span>
                </div>

                {/* 连接线 */}
                {i < steps.length - 1 && (
                  <div
                    style={{
                      width: 56,
                      height: 2,
                      marginTop: 20,
                      borderRadius: 1,
                      background: isDone || isCompleted
                        ? 'linear-gradient(90deg, #22c55e, #86efac)'
                        : '#f3f4f6',
                      transition: 'background 0.6s',
                    }}
                  />
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* ── 错误详情 ── */}
      {error && (
        <div
          style={{
            marginTop: 20,
            marginLeft: 16,
            marginRight: 16,
            padding: '10px 14px',
            borderRadius: 8,
            background: '#fef2f2',
            border: '1px solid #fecaca',
          }}
        >
          <Text style={{ fontSize: 12, color: '#dc2626' }}>{error}</Text>
        </div>
      )}
    </div>
  )
}
