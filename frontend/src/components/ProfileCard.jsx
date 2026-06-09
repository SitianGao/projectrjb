import { Card, Tag, Descriptions, Progress, Space, Typography, Tooltip } from 'antd'
import {
  BookOutlined,
  StarOutlined,
  TrophyOutlined,
  FieldTimeOutlined,
  BulbOutlined,
  UserOutlined,
  IdcardOutlined,
} from '@ant-design/icons'
import { formatPercent } from '../utils/format'

const { Text, Title } = Typography

/**
 * 学生画像卡片
 *
 * @param {Object} props
 * @param {Object} props.profile - 画像数据
 * @param {string} props.profile.name - 学生姓名
 * @param {Array<string>} props.profile.strengths - 优势学科
 * @param {Array<string>} props.profile.weaknesses - 薄弱学科
 * @param {string} props.profile.style - 学习风格
 * @param {string} props.profile.level - 当前水平
 * @param {number} props.profile.progress - 整体进度 0-100
 * @param {Array} props.profile.topics - 知识点掌握情况
 * @param {boolean} props.loading - 加载中
 */
export default function ProfileCard({ profile, loading = false }) {
  if (!profile && !loading) {
    return (
      <Card
        style={{
          borderRadius: 12,
          textAlign: 'center',
          padding: '24px 0',
          border: '1px solid var(--border, #e5e4e7)',
          background: 'rgba(255,255,255,0.7)',
          backdropFilter: 'blur(6px)',
          minHeight: 280,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div>
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: 16,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 28,
              color: '#fff',
              background: 'linear-gradient(135deg, #aa3bff 0%, #6366f1 100%)',
              boxShadow: '0 6px 20px rgba(170,59,255,0.3)',
              marginBottom: 16,
            }}
          >
            <IdcardOutlined />
          </div>
          <br />
          <Text style={{ color: '#595959', fontSize: 14 }}>
            暂无画像数据
          </Text>
          <br />
          <Text style={{ color: '#8c8c8c', fontSize: 12 }}>
            在左侧对话区与助手聊聊，完善你的学习画像
          </Text>
        </div>
      </Card>
    )
  }

  const levelColorMap = {
    初级: 'blue',
    中级: 'orange',
    高级: 'red',
  }

  return (
    <Card
      loading={loading}
      title={
        <Space>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 7,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 14,
              color: '#fff',
              background: 'linear-gradient(135deg, #aa3bff 0%, #6366f1 100%)',
            }}
          >
            <IdcardOutlined />
          </div>
          <Title level={5} style={{ margin: 0, color: 'var(--text-h, #08060d)' }}>
            学生画像
          </Title>
        </Space>
      }
      style={{
        borderRadius: 12,
        border: '1px solid var(--border, #e5e4e7)',
        background: 'rgba(255,255,255,0.7)',
        backdropFilter: 'blur(6px)',
      }}
      className="tech-profile-card"
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 基本信息 */}
        {profile?.name && (
          <div
            style={{
              background: 'rgba(170,59,255,0.03)',
              borderRadius: 10,
              padding: 12,
              border: '1px solid rgba(170,59,255,0.08)',
            }}
          >
            <Descriptions column={2} size="small" bordered={false}>
              <Descriptions.Item
                label={<Text style={{ color: '#8c8c8c', fontSize: 12 }}>姓名</Text>}
              >
                <Text strong style={{ color: '#2c2c2c' }}>
                  {profile.name}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item
                label={<Text style={{ color: '#8c8c8c', fontSize: 12 }}>学习风格</Text>}
              >
                <Tag
                  icon={<BulbOutlined />}
                  color="purple"
                  style={{
                    borderRadius: 4,
                    background: 'rgba(170,59,255,0.1)',
                    border: '1px solid rgba(170,59,255,0.3)',
                    color: '#7c3aed',
                  }}
                >
                  {profile.style || '--'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item
                label={<Text style={{ color: '#8c8c8c', fontSize: 12 }}>当前水平</Text>}
              >
                <Tag
                  color={levelColorMap[profile.level] || 'default'}
                  style={{ borderRadius: 4 }}
                >
                  {profile.level || '--'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item
                label={<Text style={{ color: '#8c8c8c', fontSize: 12 }}>整体进度</Text>}
              >
                <Progress
                  percent={profile.progress || 0}
                  size="small"
                  strokeColor={{ '0%': '#aa3bff', '100%': '#6366f1' }}
                  trailColor="rgba(0,0,0,0.06)"
                  style={{ minWidth: 100, maxWidth: '100%' }}
                />
              </Descriptions.Item>
            </Descriptions>
          </div>
        )}

        {/* 优势与薄弱 */}
        <div
          style={{
            background: 'rgba(82,196,26,0.03)',
            borderRadius: 10,
            padding: '10px 14px',
            border: '1px solid rgba(82,196,26,0.1)',
          }}
        >
          <div style={{ marginBottom: 4 }}>
            <TrophyOutlined style={{ color: '#52c41a', marginRight: 6 }} />
            <Text strong style={{ color: '#2c2c2c', fontSize: 13 }}>
              优势学科
            </Text>
          </div>
          <Space wrap style={{ marginTop: 4 }}>
            {profile?.strengths?.length > 0 ? (
              profile.strengths.map((s) => (
                <Tag
                  key={s}
                  style={{
                    borderRadius: 4,
                    background: 'rgba(82,196,26,0.1)',
                    border: '1px solid rgba(82,196,26,0.25)',
                    color: '#389e0d',
                  }}
                >
                  {s}
                </Tag>
              ))
            ) : (
              <Tag
                color="default"
                style={{ borderRadius: 4, borderStyle: 'dashed' }}
              >
                待分析
              </Tag>
            )}
          </Space>
        </div>

        <div
          style={{
            background: 'rgba(250,140,22,0.03)',
            borderRadius: 10,
            padding: '10px 14px',
            border: '1px solid rgba(250,140,22,0.1)',
          }}
        >
          <div style={{ marginBottom: 4 }}>
            <FieldTimeOutlined style={{ color: '#fa8c16', marginRight: 6 }} />
            <Text strong style={{ color: '#2c2c2c', fontSize: 13 }}>
              薄弱学科
            </Text>
          </div>
          <Space wrap style={{ marginTop: 4 }}>
            {profile?.weaknesses?.length > 0 ? (
              profile.weaknesses.map((w) => (
                <Tag
                  key={w}
                  style={{
                    borderRadius: 4,
                    background: 'rgba(250,140,22,0.1)',
                    border: '1px solid rgba(250,140,22,0.25)',
                    color: '#d46b08',
                  }}
                >
                  {w}
                </Tag>
              ))
            ) : (
              <Tag
                color="default"
                style={{ borderRadius: 4, borderStyle: 'dashed' }}
              >
                待分析
              </Tag>
            )}
          </Space>
        </div>

        {/* 知识点掌握 */}
        {profile?.topics?.length > 0 && (
          <div
            style={{
              background: 'rgba(170,59,255,0.03)',
              borderRadius: 10,
              padding: '10px 14px',
              border: '1px solid rgba(170,59,255,0.08)',
            }}
          >
            <div style={{ marginBottom: 8 }}>
              <StarOutlined style={{ color: '#aa3bff', marginRight: 6 }} />
              <Text strong style={{ color: '#2c2c2c', fontSize: 13 }}>
                知识点掌握
              </Text>
            </div>
            {profile.topics.map((topic) => {
              const pct = Math.round(
                topic.accuracy > 1 ? topic.accuracy : topic.accuracy * 100,
              )
              return (
                <Tooltip
                  key={topic.name}
                  title={`正确率: ${formatPercent(topic.accuracy)}`}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      marginBottom: 10,
                    }}
                  >
                    <BookOutlined style={{ color: '#aa3bff', fontSize: 13 }} />
                    <Text style={{ minWidth: 72, color: '#2c2c2c', fontSize: 13 }}>
                      {topic.name}
                    </Text>
                    <Progress
                      percent={pct}
                      size="small"
                      showInfo={false}
                      strokeColor={
                        pct >= 80
                          ? { '0%': '#52c41a', '100%': '#73d13d' }
                          : pct >= 60
                            ? { '0%': '#fa8c16', '100%': '#ffc53d' }
                            : { '0%': '#ff4d4f', '100%': '#ff7a45' }
                      }
                      trailColor="rgba(0,0,0,0.06)"
                      style={{ flex: 1 }}
                    />
                    <Text
                      style={{
                        fontSize: 12,
                        fontWeight: 600,
                        fontFamily: 'var(--mono, ui-monospace)',
                        color:
                          pct >= 80
                            ? '#52c41a'
                            : pct >= 60
                              ? '#fa8c16'
                              : '#ff4d4f',
                        minWidth: 32,
                        textAlign: 'right',
                      }}
                    >
                      {pct}%
                    </Text>
                  </div>
                </Tooltip>
              )
            })}
          </div>
        )}
      </Space>
    </Card>
  )
}
