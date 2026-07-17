import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Skeleton } from 'antd'
import ProfileSetupHeader from '../components/profileSetup/ProfileSetupHeader'
import ConversationPanel from '../components/profileSetup/ConversationPanel'
import LiveProfilePanel from '../components/profileSetup/LiveProfilePanel'
import ProfileConfirmationCard from '../components/profileSetup/ProfileConfirmationCard'
import AgentWorkflowCard from '../components/profileSetup/AgentWorkflowCard'
import LearningPathResultCard from '../components/profileSetup/LearningPathResultCard'
import ChatErrorCard from '../components/profileSetup/ChatErrorCard'
import { useAuth } from '../contexts/AuthContext'
import { useLiveCourseProfile } from '../hooks/useLiveCourseProfile'
import { useProfileConversation } from '../hooks/useProfileConversation'
import { useProfileConfirmation } from '../hooks/useProfileConfirmation'
import { useInitializeCourseLearning } from '../hooks/useInitializeCourseLearning'
import { useContinueLearning } from '../hooks/useContinueLearning'
import './ProfileSetupPage.css'

export default function ProfileSetupPage({ mode = 'setup' }) {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const { activeCourse, courses, updateCourse } = useAuth()
  const targetCourse = courses.find((course) => String(course.id) === String(courseId)) || activeCourse
  const resolvedCourseId = courseId || targetCourse?.id
  const { continueLearning } = useContinueLearning()

  const { profileState, loading, refresh, applyProfileResult } = useLiveCourseProfile(resolvedCourseId)
  const conversation = useProfileConversation(resolvedCourseId, { onProfileResult: applyProfileResult })
  const confirmation = useProfileConfirmation(profileState)
  const initializer = useInitializeCourseLearning({
    courseId: resolvedCourseId,
    studentId: profileState?.course?.student_id || targetCourse?.student_id,
    goal: profileState?.profile?.learning_goal || targetCourse?.goal,
  })

  useEffect(() => {
    if (!targetCourse && !loading) navigate('/courses', { replace: true })
  }, [loading, navigate, targetCourse])

  if (!targetCourse && loading) {
    return <div className="profile-setup-page"><Skeleton active paragraph={{ rows: 12 }} /></div>
  }

  const handleGenerate = async () => {
    const goal = profileState?.profile?.learning_goal || targetCourse?.goal || targetCourse?.title
    if (resolvedCourseId && goal) {
      updateCourse(resolvedCourseId, { title: goal.slice(0, 24), goal }).catch(() => {})
    }
    const path = await initializer.start()
    if (path) refresh().catch(() => {})
  }

  return (
    <div className="profile-setup-page">
      <div className="profile-setup-container">
        <ProfileSetupHeader
          course={profileState?.course || targetCourse}
          mode={mode}
          completion={profileState?.completion_rate || 0}
          onBack={() => navigate('/home')}
          onPath={() => navigate(resolvedCourseId ? `/course/${resolvedCourseId}/path` : '/courses')}
        />

        <div className="profile-setup-grid">
          <ConversationPanel
            messages={conversation.messages}
            loading={conversation.loading}
            error={conversation.error}
            onSend={conversation.send}
          />
          <div className="profile-right-stack">
            <LiveProfilePanel profileState={profileState} loading={loading} />
            <ProfileConfirmationCard
              ready={confirmation.ready}
              confirmed={confirmation.confirmed}
              onConfirmChange={confirmation.setConfirmed}
              onGenerate={handleGenerate}
              loading={initializer.loading}
              summary={confirmation.summary}
            />
            <ChatErrorCard error={initializer.error} />
            {(initializer.loading || initializer.job.status !== 'created') && (
              <AgentWorkflowCard job={initializer.job} />
            )}
            <LearningPathResultCard
              result={initializer.result}
              onEnterCourse={() => continueLearning(resolvedCourseId)}
              onViewPath={() => navigate(`/course/${resolvedCourseId}/path`)}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
