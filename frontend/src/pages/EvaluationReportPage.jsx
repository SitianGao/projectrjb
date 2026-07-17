import { Alert, Button, Card, Result, Skeleton, Typography, message } from 'antd'
import { useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import EvaluationContextBar from '../components/evaluation/EvaluationContextBar'
import EvaluationDimensionCards from '../components/evaluation/EvaluationDimensionCards'
import EvaluationEmptyState from '../components/evaluation/EvaluationEmptyState'
import EvaluationHeader from '../components/evaluation/EvaluationHeader'
import EvaluationHistoryTable from '../components/evaluation/EvaluationHistoryTable'
import EvaluationTrendChart from '../components/evaluation/EvaluationTrendChart'
import KnowledgeDiagnosisSection from '../components/evaluation/KnowledgeDiagnosisSection'
import OverallDiagnosisCard from '../components/evaluation/OverallDiagnosisCard'
import PathAdjustmentPanel from '../components/evaluation/PathAdjustmentPanel'
import CourseProgressOverview from '../components/evaluation/CourseProgressOverview'
import RegenerateEvaluationModal from '../components/evaluation/RegenerateEvaluationModal'
import useEvaluationHistory from '../hooks/useEvaluationHistory'
import useEvaluationPathAdjustment from '../hooks/useEvaluationPathAdjustment'
import useEvaluationReport from '../hooks/useEvaluationReport'
import useEvaluationScope from '../hooks/useEvaluationScope'
import useRegenerateEvaluation from '../hooks/useRegenerateEvaluation'
import { useAuth } from '../contexts/AuthContext'
import './EvaluationReportPage.css'

const { Paragraph, Title } = Typography

function activeTab(pathname) {
  if (pathname.includes('/history')) return 'history'
  if (pathname.includes('/report')) return 'report'
  return 'tests'
}

export default function EvaluationReportPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { reportId } = useParams()
  const { studentId, activeCourse, courses } = useAuth()
  const [modalOpen, setModalOpen] = useState(false)
  const scopeState = useEvaluationScope({ activeCourse, courses })
  const courseStudentId = scopeState.course?.student_id || studentId
  const reportState = useEvaluationReport({
    studentId: courseStudentId,
    courseId: scopeState.courseId,
    scope: scopeState.scope,
    reportId,
  })
  const historyState = useEvaluationHistory({ studentId: courseStudentId, courseId: scopeState.courseId })
  const regenerateState = useRegenerateEvaluation()
  const adjustmentState = useEvaluationPathAdjustment()
  const tab = activeTab(location.pathname)
  const report = reportState.report

  const trendNote = useMemo(() => {
    const overall = report?.overall || {}
    if (overall.short_term_trend === 'recovering') {
      return `较上次提升 ${overall.score_delta} 分，但仍低于本周期平均分 ${overall.period_average} 分。`
    }
    return null
  }, [report])

  function changeTab(key) {
    if (key === 'tests') navigate('/assessment/tests')
    if (key === 'report') navigate(scopeState.courseId ? `/course/${scopeState.courseId}/assessment/report` : '/assessment/report')
    if (key === 'history') navigate('/assessment/history')
  }

  async function handleRegenerate(force = false) {
    if (!scopeState.courseId || !courseStudentId) return
    const next = await regenerateState.regenerate({
      student_id: courseStudentId,
      course_id: scopeState.courseId,
      scope_type: scopeState.scope,
      force,
    })
    if (next) reportState.setReport(next)
    await historyState.reload()
    setModalOpen(false)
  }

  function renderTests() {
    return (
      <Card className="evaluation-card">
        <Title level={3}>在线测评</Title>
        <Paragraph>这里用于承载当前课程的专项练习和阶段测评；评估报告只负责展示 EvaluateAgent 的诊断结果。</Paragraph>
        <Button type="primary" onClick={() => navigate(scopeState.courseId ? `/course/${scopeState.courseId}/test` : '/evaluate')}>
          进入当前课程测评
        </Button>
      </Card>
    )
  }

  function renderHistory() {
    return (
      <Card className="evaluation-card" title="测评历史">
        <EvaluationHistoryTable history={historyState.history} loading={historyState.loading} />
      </Card>
    )
  }

  function renderReport() {
    if (reportState.loading) return <Skeleton active paragraph={{ rows: 14 }} />
    if (reportState.error) {
      return <Result status="error" title="评估报告加载失败" subTitle={reportState.error} extra={<Button type="primary" onClick={reportState.reload}>重试</Button>} />
    }
    if (!report) {
      return <EvaluationEmptyState onGenerate={() => setModalOpen(true)} loading={regenerateState.regenerating} />
    }
    return (
      <>
        <EvaluationContextBar report={report} />
        {report.overall?.confidence < 0.55 && (
          <Alert
            className="evaluation-alert"
            type="warning"
            showIcon
            message="当前评估置信度较低"
            description={`目前仅收集到 ${report.dataSummary?.questions_answered || 0} 道练习数据，建议完成更多学习任务后再次评估。`}
          />
        )}
        {trendNote && <Alert className="evaluation-alert" type="info" showIcon message="趋势说明" description={trendNote} />}
        <OverallDiagnosisCard
          report={report}
          onReview={() => navigate('/resources')}
          onPath={() => navigate(scopeState.courseId ? `/course/${scopeState.courseId}/path` : '/courses')}
          onTutor={() => navigate(scopeState.courseId ? `/course/${scopeState.courseId}/chat` : '/profile')}
        />
        <EvaluationDimensionCards dimensions={report.dimensionCards} />
        <KnowledgeDiagnosisSection
          strengths={report.strengths}
          weaknesses={report.weaknesses}
          onAction={(action, item) => {
            if (action.type === 'ai_tutor') navigate(scopeState.courseId ? `/course/${scopeState.courseId}/chat` : '/profile')
            else message.info(`${item.name}：${action.title}`)
          }}
        />
        <EvaluationTrendChart history={report.history} overall={report.overall} />
        <CourseProgressOverview progress={report.courseProgress} onGeneratePath={() => navigate(scopeState.courseId ? `/course/${scopeState.courseId}/path` : '/courses')} />
        <PathAdjustmentPanel
          items={report.pathAdjustments}
          loading={adjustmentState.loading}
          onPreview={() => adjustmentState.preview(report.evaluationId).then((res) => message.info(res.message || '已生成调整预览'))}
          onAccept={() => adjustmentState.apply(report.evaluationId)}
        />
        <Card className="evaluation-card" title="评估历史">
          <EvaluationHistoryTable history={historyState.history} loading={historyState.loading} />
        </Card>
      </>
    )
  }

  return (
    <div className="evaluation-page">
      <div className="evaluation-container">
        <EvaluationHeader
          activeKey={tab}
          onTabChange={changeTab}
          courses={courses}
          courseId={scopeState.courseId}
          onCourseChange={scopeState.setSelectedCourseId}
          scope={scopeState.scope}
          scopeOptions={scopeState.scopeOptions}
          onScopeChange={scopeState.setScope}
          onRegenerate={() => setModalOpen(true)}
          regenerating={regenerateState.regenerating}
          reportMode={!!reportId}
        />
        {tab === 'tests' ? renderTests() : tab === 'history' ? renderHistory() : renderReport()}
      </div>
      <RegenerateEvaluationModal
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => handleRegenerate(false)}
        loading={regenerateState.regenerating}
      />
    </div>
  )
}
