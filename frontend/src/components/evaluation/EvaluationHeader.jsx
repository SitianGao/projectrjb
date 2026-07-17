import { Button, Select, Space, Tabs, Typography } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

export default function EvaluationHeader({
  activeKey,
  onTabChange,
  courses = [],
  courseId,
  onCourseChange,
  scope,
  scopeOptions,
  onScopeChange,
  onRegenerate,
  regenerating,
  reportMode,
}) {
  return (
    <div className="evaluation-header">
      <div>
        <Title level={2}>学习评估报告</Title>
        <Text>基于你的学习任务、练习、测评和错题数据生成个性化诊断。</Text>
      </div>
      <Space wrap>
        <Select
          value={courseId}
          onChange={onCourseChange}
          style={{ width: 180 }}
          options={courses.map((course) => ({ label: course.title, value: course.id }))}
          placeholder="切换课程"
          disabled={reportMode}
        />
        <Select
          value={scope}
          onChange={onScopeChange}
          style={{ width: 150 }}
          options={scopeOptions}
          disabled={reportMode}
        />
        <Button type="primary" icon={<ReloadOutlined />} onClick={onRegenerate} loading={regenerating}>
          重新评估
        </Button>
      </Space>
      <Tabs
        activeKey={activeKey}
        onChange={onTabChange}
        items={[
          { key: 'tests', label: '在线测评' },
          { key: 'report', label: '评估报告' },
          { key: 'history', label: '测评历史' },
        ]}
      />
    </div>
  )
}
