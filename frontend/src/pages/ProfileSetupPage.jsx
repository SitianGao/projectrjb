import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Skeleton } from 'antd'
import ConversationPanel from '../components/profileSetup/ConversationPanel'
import LiveProfilePanel from '../components/profileSetup/LiveProfilePanel'
import { useAuth } from '../contexts/AuthContext'
import { useLiveCourseProfile } from '../hooks/useLiveCourseProfile'
import { useProfileConversation } from '../hooks/useProfileConversation'
import { useInitializeCourseLearning } from '../hooks/useInitializeCourseLearning'
import './ProfileSetupPage.css'

export default function ProfileSetupPage() {
  const { courseId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { activeCourse, courses, updateCourse } = useAuth()
  const targetCourse = courses.find((course) => String(course.id) === String(courseId)) || activeCourse
  const resolvedCourseId = courseId || targetCourse?.id
  const [highlightKeys, setHighlightKeys] = useState([])

  const { profileState, loading, refresh, applyProfileResult: applyProfileState } = useLiveCourseProfile(resolvedCourseId)
  const applyProfileResult = (result) => {
    applyProfileState(result)
    const keys = Object.keys(result?.profile_patch || {}).filter((key) => key !== 'completeness')
    if (keys.length) {
      setHighlightKeys(keys)
      window.setTimeout(() => setHighlightKeys([]), 2600)
    }
  }
  const conversation = useProfileConversation(resolvedCourseId, {
    onProfileResult: applyProfileResult,
    initialConversationId: searchParams.get('conversationId'),
  })
  const initializer = useInitializeCourseLearning({
    courseId: resolvedCourseId,
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
      updateCourse(resolvedCourseId, { goal }).catch(() => {})
    }
    const path = await initializer.start()
    if (path) {
      refresh().catch(() => {})
      navigate(`/course/${resolvedCourseId}/path`, { replace: true })
    }
  }

  return (
    <div className="profile-setup-page">
      <div className="profile-setup-grid">
        <ConversationPanel
          title="AI 学习画像助手"
          description="通过自然对话，让 AI 了解你的基础、目标和学习偏好。"
          messages={conversation.messages}
          loading={conversation.loading}
          error={conversation.error}
          onSend={conversation.send}
        />
        <LiveProfilePanel
          profileState={profileState}
          loading={loading}
          highlightKeys={highlightKeys}
          generating={initializer.loading}
          generationJob={initializer.job}
          generationError={initializer.error}
          onConfirm={handleGenerate}
        />
      </div>
    </div>
  )
}
