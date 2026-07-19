import { Button, Card, Progress, Space, Tag, Typography } from 'antd'
import {
  FileTextOutlined, FormOutlined, ApartmentOutlined,
  CodeOutlined, PlayCircleOutlined, RightOutlined,
} from '@ant-design/icons'

const { Text, Title } = Typography

const QUICK_GEN = [
  { key: 'document', label: '核心讲义', icon: <FileTextOutlined /> },
  { key: 'exercise', label: '专项练习', icon: <FormOutlined /> },
  { key: 'mindmap', label: '知识导图', icon: <ApartmentOutlined /> },
  { key: 'code', label: '代码案例', icon: <CodeOutlined /> },
]

export default function WorkspaceRightPanel({
  currentTask, weakPoints, recentResources,
  onGenerate, onResourceClick, generating,
}) {
  return (
    <div className="workspace-right-panel">
      {/* 1. 当前学习上下文 */}
      <Card className="wrp-card" title="当前学习上下文" size="small">
        {currentTask ? (
          <>
            <Text strong>{currentTask.title}</Text>
            {currentTask.description && (
              <Text type="secondary" style={{ display: 'block', fontSize: 12, marginTop: 4 }}>
                {currentTask.description}
              </Text>
            )}
            <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              <Tag>{currentTask.difficulty || '中级'}</Tag>
              <Tag>预计 {currentTask.estimated_minutes || 25} 分钟</Tag>
            </div>
            {weakPoints && weakPoints.length > 0 && (
              <div style={{ marginTop: 10, padding: '8px 12px', background: '#FFF8E1', borderRadius: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  薄弱点：{weakPoints.map(w => typeof w === 'string' ? w : w.name).join('、')}
                </Text>
              </div>
            )}
          </>
        ) : (
          <Text type="secondary" style={{ fontSize: 12 }}>选择课程任务后显示学习上下文</Text>
        )}
      </Card>

      {/* 2. 快捷生成 */}
      <Card className="wrp-card" title="生成学习资源" size="small">
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 10 }}>
          根据当前任务和薄弱点生成
        </Text>
        <div className="wrp-gen-grid">
          {QUICK_GEN.map((item) => (
            <Button key={item.key} icon={item.icon} size="small"
              loading={generating}
              onClick={() => onGenerate?.([item.key])}>
              {item.label}
            </Button>
          ))}
        </div>
      </Card>

      {/* 3. 最近生成资源 */}
      <Card className="wrp-card" title="最近生成" size="small">
        {recentResources && recentResources.length > 0 ? (
          <div className="wrp-resource-list">
            {recentResources.map((r) => (
              <div className="wrp-resource-item" key={r.id}
                onClick={() => onResourceClick?.(r)}>
                <div>
                  <Text style={{ fontSize: 13 }}>{r.title}</Text>
                  <Text type="secondary" style={{ fontSize: 11, display: 'block' }}>
                    {r.type === 'document' ? '讲义' : r.type === 'exercise' ? '练习' : r.type === 'mindmap' ? '导图' : r.type === 'code' ? '代码' : '资源'}
                    {r.status === 'generating' ? ' · 生成中...' : ''}
                  </Text>
                </div>
                {r.status !== 'generating' && <RightOutlined style={{ color: '#9ca3af', fontSize: 12 }} />}
                {r.status === 'generating' && <Progress percent={r.progress || 50} size="small" style={{ width: 60 }} />}
              </div>
            ))}
          </div>
        ) : (
          <Text type="secondary" style={{ fontSize: 12 }}>尚未生成学习资源</Text>
        )}
      </Card>
    </div>
  )
}
