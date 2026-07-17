import client from '../api/client'

export async function getSessionBootstrap() {
  return client.get('/session/bootstrap')
}

export function resolveLoginTarget(bootstrap) {
  const courseProfile = bootstrap?.course_profile
  const learningPath = bootstrap?.learning_path
  const target = bootstrap?.continue_target?.route

  if (!bootstrap?.user?.active_course) return '/courses'
  if (courseProfile?.requires_setup) return `/course/${courseProfile.course_id}/profile/setup`
  if (courseProfile?.requires_update) return `/course/${courseProfile.course_id}/profile/update`
  if (!learningPath?.exists) return `/course/${courseProfile.course_id}/profile/setup`
  return target || '/home'
}
