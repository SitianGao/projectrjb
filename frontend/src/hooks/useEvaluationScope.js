import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { SCOPE_OPTIONS } from '../services/evaluationService'

export default function useEvaluationScope({ activeCourse, courses }) {
  const { courseId: routeCourseId } = useParams()
  const [scope, setScope] = useState('last_30_days')
  const [selectedCourseId, setSelectedCourseId] = useState(routeCourseId || activeCourse?.id || courses?.[0]?.id)

  const courseId = routeCourseId || selectedCourseId || activeCourse?.id || courses?.[0]?.id
  const course = useMemo(
    () => courses?.find((item) => String(item.id) === String(courseId)) || activeCourse || null,
    [activeCourse, courseId, courses],
  )

  return {
    scope,
    setScope,
    course,
    courseId,
    selectedCourseId,
    setSelectedCourseId,
    scopeOptions: SCOPE_OPTIONS,
    routeCourseId,
  }
}
