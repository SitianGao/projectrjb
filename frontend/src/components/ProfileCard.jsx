import { Card, Tag, Descriptions, Progress, Space, Typography, Tooltip } from 'antd'
import {
  BookOutlined,
  StarOutlined,
  TrophyOutlined,
  FieldTimeOutlined,
  BulbOutlined,
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
      <Card>
        <Text type="secondary">暂无画像数据，请先完成信息采集</Text>
      </Card>
    )
  }

  const levelColorMap = {
    初级: 'blue',
    中级: 'orange',
    高级: 'red',
  }

  return (
    <Card loading={loading} title={<Title level={4} style={{ margin: 0 }}>学生画像</Title>}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 基本信息 */}
        {profile?.name && (
          <Descriptions column={2} size="small" bordered>
            <Descriptions.Item label="姓名">{profile.name}</Descriptions.Item>
            <Descriptions.Item label="学习风格">
              <Tag icon={<BulbOutlined />} color="purple">
                {profile.style || '--'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="当前水平">
              <Tag color={levelColorMap[profile.level] || 'default'}>
                {profile.level || '--'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="整体进度">
              <Progress
                percent={profile.progress || 0}
                size="small"
                style={{ minWidth: 120 }}
              />
            </Descriptions.Item>
          </Descriptions>
        )}

        {/* 优势与薄弱 */}
        <div>
          <Text strong>
            <TrophyOutlined /> 优势学科：
          </Text>
          <Space wrap style={{ marginLeft: 8 }}>
            {profile?.strengths?.length > 0
              ? profile.strengths.map((s) => (
                  <Tag key={s} color="success">
                    {s}
                  </Tag>
                ))
              : <Text type="secondary">待分析</Text>}
          </Space>
        </div>

        <div>
          <Text strong>
            <FieldTimeOutlined /> 薄弱学科：
          </Text>
          <Space wrap style={{ marginLeft: 8 }}>
            {profile?.weaknesses?.length > 0
              ? profile.weaknesses.map((w) => (
                  <Tag key={w} color="warning">
                    {w}
                  </Tag>
                ))
              : <Text type="secondary">待分析</Text>}
          </Space>
        </div>

        {/* 知识点掌握 */}
        {profile?.topics?.length > 0 && (
          <div>
            <Text strong>
              <StarOutlined /> 知识点掌握：
            </Text>
            <div style={{ marginTop: 8 }}>
              {profile.topics.map((topic) => (
                <Tooltip key={topic.name} title={`正确率: ${formatPercent(topic.accuracy)}`}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      marginBottom: 6,
                    }}
                  >
                    <BookOutlined style={{ color: '#1677ff' }} />
                    <Text style={{ minWidth: 80 }}>{topic.name}</Text>
                    <Progress
                      percent={Math.round(topic.accuracy > 1 ? topic.accuracy : topic.accuracy * 100)}
                      size="small"
                      style={{ flex: 1 }}
                    />
                  </div>
                </Tooltip>
              ))}
            </div>
          </div>
        )}
      </Space>
    </Card>
  )
}
