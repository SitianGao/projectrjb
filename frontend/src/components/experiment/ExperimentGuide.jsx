import { Typography, Steps, Tag, Space, Collapse, Alert, List } from 'antd'
import {
  ExperimentOutlined, BulbOutlined, EyeOutlined,
  BookOutlined, WarningOutlined,
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography

/**
 * 实验指导面板 — 左侧展示实验信息、步骤导航和知识提示。
 */
export default function ExperimentGuide({
  experiment,
  currentStep = 0,
  onStepChange,
}) {
  if (!experiment) return null

  const {
    title,
    scenario,
    difficulty,
    estimated_minutes,
    learning_objectives = [],
    knowledge_points = [],
    steps = [],
    observation_questions = [],
    common_errors = [],
    expected_phenomena = [],
    personalization_reason,
  } = experiment

  const diffColor = {
    '初级': 'green', '中级': 'blue', '高级': 'red',
  }[difficulty] || 'blue'

  const stepItems = steps.map((s, i) => ({
    title: s.title,
    description: i === currentStep ? (
      <div style={{ marginTop: 4 }}>
        <Paragraph style={{ fontSize: 13, margin: 0 }}>{s.instruction}</Paragraph>
        {s.expected_result && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            预期：{s.expected_result}
          </Text>
        )}
        {s.hint && i === currentStep && (
          <Alert
            message={s.hint}
            type="info"
            showIcon
            icon={<BulbOutlined />}
            style={{ marginTop: 8, fontSize: 12 }}
          />
        )}
      </div>
    ) : null,
  }))

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 16,
      height: '100%',
      overflow: 'auto',
      paddingRight: 4,
    }}>
      {/* 标题区 */}
      <div>
        <Title level={5} style={{ margin: 0, marginBottom: 8 }}>
          <ExperimentOutlined style={{ marginRight: 8, color: '#89b4fa' }} />
          {title || '代码实验'}
        </Title>
        <Space size={8} wrap>
          <Tag color={diffColor}>{difficulty}</Tag>
          <Tag>预计 {estimated_minutes} 分钟</Tag>
        </Space>
        {scenario && (
          <Paragraph style={{ marginTop: 8, fontSize: 13, color: '#666' }}>
            {scenario}
          </Paragraph>
        )}
        {personalization_reason && (
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
            💡 {personalization_reason}
          </Text>
        )}
      </div>

      {/* 学习目标 */}
      {learning_objectives.length > 0 && (
        <Collapse
          size="small"
          defaultActiveKey={['objectives']}
          items={[{
            key: 'objectives',
            label: <Text strong style={{ fontSize: 13 }}>🎯 学习目标</Text>,
            children: (
              <List
                size="small"
                dataSource={learning_objectives}
                renderItem={(item) => (
                  <List.Item style={{ padding: '2px 0', border: 'none' }}>
                    <Text style={{ fontSize: 13 }}>• {item}</Text>
                  </List.Item>
                )}
              />
            ),
          }]}
        />
      )}

      {/* 实验步骤 */}
      {steps.length > 0 && (
        <div>
          <Text strong style={{ fontSize: 13, marginBottom: 8, display: 'block' }}>
            📋 实验步骤
          </Text>
          <Steps
            current={currentStep}
            direction="vertical"
            size="small"
            items={stepItems}
            onChange={onStepChange}
            style={{ cursor: 'pointer' }}
          />
        </div>
      )}

      {/* 观察问题 */}
      {observation_questions.length > 0 && (
        <Collapse
          size="small"
          items={[{
            key: 'observe',
            label: <Text strong style={{ fontSize: 13 }}><EyeOutlined /> 观察问题</Text>,
            children: (
              <List
                size="small"
                dataSource={observation_questions}
                renderItem={(item, i) => (
                  <List.Item style={{ padding: '2px 0', border: 'none' }}>
                    <Text style={{ fontSize: 13 }}>{i + 1}. {item}</Text>
                  </List.Item>
                )}
              />
            ),
          }]}
        />
      )}

      {/* 预期现象 */}
      {expected_phenomena.length > 0 && (
        <Collapse
          size="small"
          items={[{
            key: 'phenomena',
            label: <Text strong style={{ fontSize: 13 }}><BulbOutlined /> 预期现象</Text>,
            children: (
              <List
                size="small"
                dataSource={expected_phenomena}
                renderItem={(item) => (
                  <List.Item style={{ padding: '2px 0', border: 'none' }}>
                    <Text style={{ fontSize: 13 }}>• {item}</Text>
                  </List.Item>
                )}
              />
            ),
          }]}
        />
      )}

      {/* 常见错误 */}
      {common_errors.length > 0 && (
        <Collapse
          size="small"
          items={[{
            key: 'errors',
            label: <Text strong style={{ fontSize: 13 }}><WarningOutlined /> 常见错误</Text>,
            children: (
              <List
                size="small"
                dataSource={common_errors}
                renderItem={(item) => (
                  <List.Item style={{ padding: '2px 0', border: 'none' }}>
                    <Text type="danger" style={{ fontSize: 13 }}>⚠ {item}</Text>
                  </List.Item>
                )}
              />
            ),
          }]}
        />
      )}

      {/* 知识点 */}
      {knowledge_points.length > 0 && (
        <div>
          <Text strong style={{ fontSize: 13 }}>
            <BookOutlined /> 相关知识点
          </Text>
          <div style={{ marginTop: 4 }}>
            {knowledge_points.map((kp) => (
              <Tag key={kp} style={{ marginBottom: 4 }}>{kp}</Tag>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
