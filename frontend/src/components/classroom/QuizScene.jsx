import { Alert, Button, Radio, Space, Typography } from 'antd'
import { useClassroomQuiz } from '../../hooks/useClassroomQuiz'

const { Text } = Typography

export default function QuizScene({ scene, classroom, session }) {
  const quiz = useClassroomQuiz(classroom, session)
  return (
    <div className="quiz-scene">
      {(scene.content?.questions || []).map((question) => (
        <div className="quiz-question" key={question.question_id}>
          <Text strong>{question.question}</Text>
          <Radio.Group
            value={quiz.answers[question.question_id]}
            onChange={(event) => quiz.setAnswers((prev) => ({ ...prev, [question.question_id]: event.target.value }))}
          >
            <Space direction="vertical">
              {(question.options || []).map((option) => <Radio key={option} value={option}>{option}</Radio>)}
            </Space>
          </Radio.Group>
        </div>
      ))}
      <Button type="primary" onClick={quiz.submit}>提交测验</Button>
      {quiz.result && <Alert type="info" showIcon message={`当前课堂得分：${quiz.result.score}`} description="答错题目已自动进入当前课程错题本。" />}
    </div>
  )
}
