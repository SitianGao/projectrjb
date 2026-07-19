export const HOME_DASHBOARD_INVALIDATE_EVENT = 'home-dashboard:invalidate'

export function invalidateHomeDashboard(courseId, reason = 'learning_updated') {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(HOME_DASHBOARD_INVALIDATE_EVENT, {
    detail: {
      courseId: courseId ? String(courseId) : null,
      reason,
    },
  }))
}
