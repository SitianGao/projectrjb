import { Breadcrumb, Button, Space, Tooltip, Typography } from 'antd'
import {
  ArrowLeftOutlined,
  ExpandOutlined,
  CompressOutlined,
  EyeInvisibleOutlined,
  ShareAltOutlined,
  DownloadOutlined,
  BulbOutlined,
} from '@ant-design/icons'

const { Text, Title } = Typography

export default function ClassroomInfoBar({
  classroom,
  currentIndex,
  totalScenes,
  onBack,
  focusMode,
  onToggleFocus,
  isFullscreen,
  onToggleFullscreen,
}) {
  const currentScene = classroom?.scenes?.[currentIndex]
  const stageName = classroom?.stage_name || classroom?.title || ''

  return (
    <div
      style={{
        height: 56,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        background: 'rgba(255,255,255,0.85)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(0,0,0,0.06)',
        zIndex: 50,
      }}
    >
      {/* Left: breadcrumb + context */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, minWidth: 0 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={onBack}
          style={{ color: '#6B7280', fontWeight: 500, flexShrink: 0 }}
        >
          {focusMode ? '' : '返回'}
        </Button>

        {!focusMode && (
          <>
            <div style={{ width: 1, height: 24, background: '#E5E7EB', flexShrink: 0 }} />

            <Breadcrumb
              items={[
                { title: <span style={{ fontSize: 13, color: '#6B7280' }}>学习路径</span> },
                { title: <span style={{ fontSize: 13, color: '#6B7280' }}>{stageName || '课程'}</span> },
                {
                  title: (
                    <span style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>
                      {currentScene?.title || `场景 ${currentIndex + 1}`}
                    </span>
                  ),
                },
              ]}
              style={{ fontSize: 13 }}
            />
          </>
        )}

        {focusMode && (
          <Text style={{ fontSize: 14, fontWeight: 600, color: '#111827' }}>
            {currentScene?.title || `场景 ${currentIndex + 1}`}
          </Text>
        )}
      </div>

      {/* Right: utility buttons */}
      <Space size={4}>
        <Tooltip title={focusMode ? '退出专注模式' : '专注模式'}>
          <Button
            type="text"
            size="small"
            icon={<EyeInvisibleOutlined />}
            onClick={onToggleFocus}
            style={{
              color: focusMode ? '#6C5CE7' : '#9CA3AF',
              background: focusMode ? 'rgba(108,92,231,0.08)' : 'transparent',
              borderRadius: 8,
            }}
          />
        </Tooltip>

        <Tooltip title="分享">
          <Button
            type="text"
            size="small"
            icon={<ShareAltOutlined />}
            style={{ color: '#9CA3AF', borderRadius: 8 }}
          />
        </Tooltip>

        <Tooltip title="导出">
          <Button
            type="text"
            size="small"
            icon={<DownloadOutlined />}
            style={{ color: '#9CA3AF', borderRadius: 8 }}
          />
        </Tooltip>

        <div style={{ width: 1, height: 20, background: '#E5E7EB' }} />

        <Tooltip title={isFullscreen ? '退出全屏' : '全屏'}>
          <Button
            type="text"
            size="small"
            icon={isFullscreen ? <CompressOutlined /> : <ExpandOutlined />}
            onClick={onToggleFullscreen}
            style={{ color: '#9CA3AF', borderRadius: 8 }}
          />
        </Tooltip>
      </Space>
    </div>
  )
}
