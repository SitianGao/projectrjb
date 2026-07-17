import { Card, Tag, Space, Typography, Collapse, Descriptions, Progress } from 'antd'
import {
  CheckCircleFilled, CloseCircleFilled, ClockCircleFilled,
  BugFilled, ToolFilled, ThunderboltFilled,
} from '@ant-design/icons'

const { Text, Title } = Typography

const STATUS_CONFIG = {
  Accepted: { color: '#52c41a', icon: <CheckCircleFilled />, label: '通过', bgColor: '#f6ffed' },
  WrongAnswer: { color: '#ff4d4f', icon: <CloseCircleFilled />, label: '答案错误', bgColor: '#fff2f0' },
  TimeLimitExceeded: { color: '#faad14', icon: <ClockCircleFilled />, label: '运行超时', bgColor: '#fffbe6' },
  RuntimeError: { color: '#ff4d4f', icon: <BugFilled />, label: '运行错误', bgColor: '#fff2f0' },
  CompileError: { color: '#ff7a45', icon: <ToolFilled />, label: '编译错误', bgColor: '#fff7e6' },
}

export default function JudgeResult({ result, loading }) {
  if (loading) {
    return (
      <Card style={{ textAlign: 'center', padding: 24 }}>
        <ThunderboltFilled spin style={{ fontSize: 32, color: '#1677ff' }} />
        <Text style={{ display: 'block', marginTop: 12 }}>判题中...</Text>
      </Card>
    )
  }

  if (!result) return null

  const config = STATUS_CONFIG[result.status] || STATUS_CONFIG.RuntimeError
  const passRate = result.total > 0 ? Math.round((result.passed / result.total) * 100) : 0

  return (
    <Card
      style={{
        borderLeft: `4px solid ${config.color}`,
        background: config.bgColor,
      }}
    >
      {/* Overall Verdict */}
      <div style={{ textAlign: 'center', marginBottom: 16 }}>
        <span style={{ fontSize: 48, color: config.color }}>{config.icon}</span>
        <Title level={3} style={{ margin: '8px 0', color: config.color }}>
          {config.label}
        </Title>
        <Space size="large">
          <Text>
            通过测试用例：<Text strong>{result.passed}</Text> / {result.total}
          </Text>
          <Text>
            得分：<Text strong>{result.score ?? passRate}</Text> 分
          </Text>
          {result.total_time_ms > 0 && (
            <Text type="secondary">总耗时：{result.total_time_ms.toFixed(0)} ms</Text>
          )}
        </Space>
        <Progress
          percent={passRate}
          status={result.status === 'Accepted' ? 'success' : 'exception'}
          style={{ maxWidth: 400, margin: '12px auto 0' }}
        />
      </div>

      {/* Compile Error */}
      {result.compile_error && (
        <Card
          size="small"
          title={<><ToolFilled /> 编译错误</>}
          style={{ marginBottom: 12, background: '#fff1f0' }}
        >
          <pre style={{
            whiteSpace: 'pre-wrap', wordBreak: 'break-all',
            fontSize: 13, margin: 0, maxHeight: 200, overflow: 'auto',
          }}>
            {result.compile_error}
          </pre>
        </Card>
      )}

      {/* Per Test Case Results */}
      {result.results && result.results.length > 0 && (
        <Collapse
          size="small"
          items={[{
            key: 'details',
            label: <Text strong>测试用例详情（{result.results.length} 个）</Text>,
            children: (
              <div style={{ maxHeight: 300, overflow: 'auto' }}>
                {result.results.map((tc, idx) => {
                  const tcConfig = STATUS_CONFIG[tc.status] || STATUS_CONFIG.RuntimeError
                  return (
                    <Card
                      key={idx}
                      size="small"
                      style={{ marginBottom: 8 }}
                      title={
                        <Space>
                          <Tag color={tc.status === 'Accepted' ? 'success' : 'error'}>
                            用例 {tc.case_id !== undefined ? tc.case_id + 1 : idx + 1}
                          </Tag>
                          <span style={{ color: tcConfig.color }}>{tcConfig.icon}</span>
                          <Text style={{ color: tcConfig.color }}>{tcConfig.label}</Text>
                          {tc.time_ms > 0 && (
                            <Text type="secondary">耗时 {tc.time_ms}ms</Text>
                          )}
                        </Space>
                      }
                    >
                      {tc.status !== 'Accepted' && tc.expected && (
                        <Descriptions size="small" column={1}>
                          {tc.expected && (
                            <Descriptions.Item label="期望输出">
                              <pre style={{ margin: 0, color: '#52c41a' }}>{tc.expected}</pre>
                            </Descriptions.Item>
                          )}
                          {tc.actual && (
                            <Descriptions.Item label="实际输出">
                              <pre style={{ margin: 0, color: '#ff4d4f' }}>{tc.actual}</pre>
                            </Descriptions.Item>
                          )}
                        </Descriptions>
                      )}
                    </Card>
                  )
                })}
              </div>
            ),
          }]}
        />
      )}
    </Card>
  )
}
