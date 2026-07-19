import { Descriptions, Drawer, Tag, Typography } from 'antd'
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
  const source = pathData?.generation_source || 'legacy'
  const sourceLabels = {
    agent: 'AI 智能规划生成',
    seed: '演示预置数据',
    manual: '人工配置',
    rule_fallback: '规则降级生成',
    legacy: '历史路径（来源未记录）',
  }

  return (
    <Drawer
      title="查看生成依据"
      open={visible}
      onClose={onClose}
      width={480}
      styles={{ body: { padding: '20px 24px' } }}
    >
      <div style={{ marginBottom: 20 }}>
        <Text strong style={{ fontSize: 14, color: '#111827', display: 'block', marginBottom: 8 }}>
          <BulbOutlined style={{ color: '#6C5CE7', marginRight: 6 }} />
          路径来源
        </Text>
        <Descriptions size="small" column={1} bordered>
          <Descriptions.Item label="路径来源">{sourceLabels[source] || source}</Descriptions.Item>
          <Descriptions.Item label="画像版本">
            {pathData?.profile_version ? `v${pathData.profile_version}` : '未记录'}
          </Descriptions.Item>
          <Descriptions.Item label="路径版本">v{pathData?.version || 1}</Descriptions.Item>
          <Descriptions.Item label="规则降级">
            <Tag color={pathData?.fallback_used ? 'orange' : 'green'}>
              {pathData?.fallback_used ? '是' : '否'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="生成时间">{pathData?.generated_at || pathData?.created_at || '未记录'}</Descriptions.Item>
        </Descriptions>
        <Paragraph style={{ fontSize: 13, color: '#6B7280', lineHeight: 1.7, marginTop: 12 }}>
          {source === 'seed'
            ? '当前路径来自数据库中的演示预置数据，用于稳定展示历史学习记录；它不会被标记为大模型生成。'
            : source === 'agent'
              ? '当前路径由 PlannerAgent 基于课程画像、学习目标和课程知识库生成，并已保存到数据库。'
              : source === 'rule_fallback'
                ? '模型调用未成功，本路径由开发模式规则生成；严格录制模式下不会允许这种降级。'
                : '这是一条旧版本路径，历史数据没有记录可靠的生成来源，因此不会推断为 Agent 生成。'}
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
                阶段{stage.order || si + 1}：{stage.title}
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

      {source === 'agent' && (
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
      )}
    </Drawer>
  )
}
