import { Button, Result, Space, Statistic } from 'antd'
import { useNavigate } from 'react-router-dom'

export default function ClassroomCompletionResult({ courseId, result }) {
  const navigate = useNavigate()
  const evaluation = result?.evaluation_result?.classroom_evaluation || result?.classroom_evaluation || {}

  return (
    <Result
      className="classroom-completion"
      status="success"
      title="互动课堂已完成"
      subTitle="学习记录、课堂表现和画像更新已写入当前课程。"
      extra={[
        <Space key="stats" size={24} wrap>
          <Statistic title="理解度" value={Math.round((evaluation.understanding || 0) * 100)} suffix="%" />
          <Statistic title="参与度" value={Math.round((evaluation.engagement || 0) * 100)} suffix="%" />
          <Statistic title="建议强度" value={evaluation.recommendation || '继续巩固'} />
        </Space>,
        <Button key="path" type="primary" onClick={() => navigate(`/course/${courseId}/path`)}>查看更新后的学习路径</Button>,
        <Button key="home" onClick={() => navigate('/home')}>返回学习首页</Button>,
      ]}
    />
  )
}
