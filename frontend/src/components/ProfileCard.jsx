import { Card, Tag, Progress, Space, Typography, Descriptions, Empty } from 'antd'
import {
  BookOutlined,
  AimOutlined,
  BulbOutlined,
  WarningOutlined,
  HeartOutlined,
  DashboardOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'

const { Text, Title } = Typography

/**
 * 学生画像卡片 —— 匹配后端 6 维画像格式
 *
 * 后端返回格式:
 * {
 *   student_id, profile: { knowledge_level, learning_goal, cognitive_style,
 *     weakness[], interest[], pace_preference, learning_history[] },
 *   completeness, confidence, sources, next_questions
 * }
 */
export default function ProfileCard({ profile, loading = false }) {
  // 无数据且未加载中
  if (!profile && !loading) {
    return (
      <Card>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无画像数据，请在左侧对话中描述你的学习情况"
        />
      </Card>
    )
  }

  // 提取画像（兼容两种嵌套方式）
  const inner = profile?.profile || profile || {}
  const kl = inner.knowledge_level || ''
  const goal = inner.learning_goal || ''
  const style = inner.cognitive_style || ''
  const weakness = inner.weakness || []
  const interest = inner.interest || []
  const pace = inner.pace_preference || '中速均衡型'
  const completeness = profile?.completeness ?? inner?.completeness ?? 0
  const confidence = profile?.confidence ?? inner?.confidence ?? 0
  const nextQuestions = profile?.next_questions ?? inner?.next_questions ?? []

  // 知识水平 → 颜色映射
  const levelColorMap = {
    '零基础': '#8c8c8c',
    '初级': '#1677ff',
    '中级': '#fa8c16',
    '中高级': '#722ed1',
    '高级': '#f5222d',
  }
  const levelColor = Object.entries(levelColorMap).find(([k]) => kl.includes(k))?.[1] || '#1677ff'

  // 学习节奏 → 图标
  const paceIcon = {
    '快速': '🚀',
    '慢速': '🐢',
    '中速': '⚖️',
  }
  const paceEmoji = Object.entries(paceIcon).find(([k]) => pace.includes(k))?.[1] || '⚖️'

  // 置信度颜色
  const confidenceColor = confidence >= 0.85 ? '#52c41a' : confidence >= 0.7 ? '#faad14' : '#ff4d4f'

  return (
    <Card
      loading={loading}
      title={
        <Space>
          <Title level={4} style={{ margin: 0 }}>📊 学生画像</Title>
          {confidence > 0 && (
            <Tag color={confidenceColor}>
              置信度 {(confidence * 100).toFixed(0)}%
            </Tag>
          )}
        </Space>
      }
      extra={
        completeness > 0 && (
          <Progress
            type="circle"
            percent={Math.round(completeness * 100)}
            size={48}
            strokeColor="#1677ff"
            format={(p) => `${p}%`}
          />
        )
      }
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 知识水平 + 学习节奏 */}
        <Descriptions column={1} size="small" bordered>
          <Descriptions.Item
            label={<><BookOutlined /> 知识水平</>}
          >
            <Tag color={levelColor} style={{ fontSize: 13 }}>
              {kl || '待分析'}
            </Tag>
          </Descriptions.Item>

          <Descriptions.Item
            label={<><AimOutlined /> 学习目标</>}
          >
            <Text>{goal || '待明确'}</Text>
          </Descriptions.Item>

          <Descriptions.Item
            label={<><BulbOutlined /> 认知风格</>}
          >
            <Tag color="purple">{style || '待分析'}</Tag>
          </Descriptions.Item>

          <Descriptions.Item
            label={<><DashboardOutlined /> 学习节奏</>}
          >
            <Text>{paceEmoji} {pace}</Text>
          </Descriptions.Item>
        </Descriptions>

        {/* 兴趣方向 */}
        <div>
          <Text strong><HeartOutlined /> 兴趣方向：</Text>
          <div style={{ marginTop: 6 }}>
            {interest.length > 0 ? (
              <Space wrap>
                {interest.map((item) => (
                  <Tag key={item} color="magenta">{item}</Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary">待发现</Text>
            )}
          </div>
        </div>

        {/* 薄弱点 */}
        <div>
          <Text strong><WarningOutlined /> 薄弱点：</Text>
          <div style={{ marginTop: 6 }}>
            {weakness.length > 0 ? (
              <Space wrap>
                {weakness.map((item) => (
                  <Tag key={item} color="warning">{item}</Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary">暂未发现薄弱点</Text>
            )}
          </div>
        </div>

        {/* 下一步追问 */}
        {nextQuestions.length > 0 && (
          <div
            style={{
              background: '#f6f8fa',
              borderRadius: 8,
              padding: '10px 14px',
              border: '1px solid #e8e8e8',
            }}
          >
            <Text strong><CheckCircleOutlined /> 建议追问：</Text>
            <div style={{ marginTop: 4 }}>
              {nextQuestions.map((q, i) => (
                <Text key={i} type="secondary" style={{ display: 'block', fontSize: 13 }}>
                  {i + 1}. {q}
                </Text>
              ))}
            </div>
          </div>
        )}
      </Space>
    </Card>
  )
}
