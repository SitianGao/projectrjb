import { Card, Tag, Space, Typography, Divider } from 'antd'
import { ClockCircleOutlined, TagOutlined } from '@ant-design/icons'
import MarkdownRenderer from './MarkdownRenderer'

const { Text, Title } = Typography

const DIFFICULTY_MAP = {
  '简单': { color: 'success', label: '简单' },
  '中等': { color: 'warning', label: '中等' },
  '困难': { color: 'error', label: '困难' },
}

export default function ProblemPanel({ problem, loading }) {
  if (loading) {
    return <Card loading style={{ minHeight: 300 }} />
  }

  if (!problem) {
    return (
      <Card>
        <Text type="secondary">请从左侧选择一道编程题开始练习</Text>
      </Card>
    )
  }

  const diff = DIFFICULTY_MAP[problem.difficulty] || DIFFICULTY_MAP['中等']

  return (
    <Card
      title={
        <Space wrap>
          <Title level={4} style={{ margin: 0 }}>{problem.title}</Title>
          <Tag color={diff.color}>{diff.label}</Tag>
        </Space>
      }
      extra={
        <Space>
          {problem.suggested_minutes && (
            <Text type="secondary">
              <ClockCircleOutlined /> {problem.suggested_minutes}
            </Text>
          )}
        </Space>
      }
      style={{ height: '100%', overflow: 'auto' }}
    >
      {/* Tags */}
      {problem.tags && problem.tags.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <TagOutlined style={{ marginRight: 4 }} />
          {problem.tags.map((tag) => (
            <Tag key={tag}>{tag}</Tag>
          ))}
        </div>
      )}

      {/* Description */}
      {problem.description && (
        <>
          <Text strong>题目描述</Text>
          <div style={{ marginTop: 8, marginBottom: 16 }}>
            <MarkdownRenderer content={problem.description} compact />
          </div>
        </>
      )}

      <Divider />

      {/* Input Format */}
      {problem.input_format && (
        <>
          <Text strong>输入格式</Text>
          <div style={{ marginTop: 8, marginBottom: 16 }}>
            <MarkdownRenderer content={problem.input_format} compact />
          </div>
        </>
      )}

      {/* Output Format */}
      {problem.output_format && (
        <>
          <Text strong>输出格式</Text>
          <div style={{ marginTop: 8, marginBottom: 16 }}>
            <MarkdownRenderer content={problem.output_format} compact />
          </div>
        </>
      )}

      {/* Sample I/O */}
      {problem.sample_input && (
        <>
          <Divider />
          <Text strong>输入样例</Text>
          <pre style={{
            background: 'var(--bg-page)',
            padding: 12,
            borderRadius: 6,
            fontSize: 13,
            marginTop: 8,
          }}>
            {problem.sample_input}
          </pre>
        </>
      )}

      {problem.sample_output && (
        <>
          <Text strong>输出样例</Text>
          <pre style={{
            background: 'var(--bg-page)',
            padding: 12,
            borderRadius: 6,
            fontSize: 13,
            marginTop: 8,
          }}>
            {problem.sample_output}
          </pre>
        </>
      )}

      {/* Test case count */}
      {problem.test_case_count > 0 && (
        <Text type="secondary" style={{ display: 'block', marginTop: 16 }}>
          本题共有 {problem.test_case_count} 个测试用例（含样例），全部通过方可获得满分。
        </Text>
      )}
    </Card>
  )
}
