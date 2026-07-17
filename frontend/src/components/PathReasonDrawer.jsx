import { Drawer, Tag, Typography } from 'antd'
import { BookOutlined, BranchesOutlined, BulbOutlined } from '@ant-design/icons'

const { Text, Paragraph } = Typography

/**
 * Drawer explaining why the learning path was generated this way.
 * Shows the algorithm, data sources, and knowledge base references.
 */
export default function PathReasonDrawer({
  visible,
  onClose,
  pathData,
}) {
  const stages = pathData?.stages || []
  const totalSources = stages.reduce(
    (sum, s) => sum + (Array.isArray(s.knowledge_sources) ? s.knowledge_sources.length : 0), 0,
  )

  return (
    <Drawer
      title="为什么这样规划？"
      open={visible}
      onClose={onClose}
      width={480}
      styles={{ body: { padding: '20px 24px' } }}
    >
      {/* How it works */}
      <div style={{ marginBottom: 20 }}>
        <Text strong style={{ fontSize: 14, color: '#111827', display: 'block', marginBottom: 8 }}>
          <BulbOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />
          路径生成原理
        </Text>
        <Paragraph style={{ fontSize: 13, color: '#6B7280', lineHeight: 1.7 }}>
          系统根据你的学习画像（知识基础、学习目标、薄弱点、兴趣方向、认知风格）、
          课程知识库结构和学习记录，通过 PlannerAgent 自动规划阶段递进路径。
          每个阶段遵循"先基础后进阶"的认知逻辑，并参考艾宾浩斯遗忘曲线安排复习节点。
        </Paragraph>
      </div>

      {/* Data sources */}
      <div style={{ marginBottom: 20 }}>
        <Text strong style={{ fontSize: 14, color: '#111827', display: 'block', marginBottom: 8 }}>
          <BookOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />
          数据来源（{totalSources} 条）
        </Text>
        {stages.map((stage, si) => {
          const sources = Array.isArray(stage.knowledge_sources) ? stage.knowledge_sources : []
          if (!sources.length) return null
          return (
            <div key={si} style={{ marginBottom: 10 }}>
              <Text style={{ fontSize: 12, color: '#9CA3AF', display: 'block', marginBottom: 4 }}>
                阶段{stage.stage_id}：{stage.title}
              </Text>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {sources.slice(0, 5).map((src, i) => (
                  <Tag key={i} color="purple" style={{ fontSize: 11, borderRadius: 6 }}>
                    {src.title || src.source}
                  </Tag>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Algorithm */}
      <div>
        <Text strong style={{ fontSize: 14, color: '#111827', display: 'block', marginBottom: 8 }}>
          <BranchesOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />
          规划策略
        </Text>
        <div style={{ fontSize: 13, color: '#6B7280', lineHeight: 1.7 }}>
          <p>• 认知递进：从基础概念到高级应用，避免跳跃式学习</p>
          <p>• 薄弱点优先：评估中发现的薄弱知识点排在路径前列</p>
          <p>• 间隔复习：基于艾宾浩斯遗忘曲线计算记忆保持率</p>
          <p>• 自适应调整：每次评估后动态调整后续阶段安排</p>
        </div>
      </div>
    </Drawer>
  )
}
