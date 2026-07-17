/**
 * Safe numeric clamping utilities.
 * Prevents NaN, negative values, completed > total, and progress > 100%.
 */

export function safeClamp(value, min = 0, max = Infinity) {
  const num = Number(value)
  if (!Number.isFinite(num)) return min
  return Math.max(min, Math.min(num, max))
}

export function safeProgress(completed, total) {
  const safeTotal = Math.max(0, Number(total) || 0)
  const safeCompleted = safeClamp(Number(completed) || 0, 0, safeTotal)
  const percent = safeTotal > 0 ? Math.round((safeCompleted / safeTotal) * 100) : 0
  return { completed: safeCompleted, total: safeTotal, percent }
}

/** Deduplicate tasks by id, preventing double-counting */
export function dedupeTasks(tasks = []) {
  const seen = new Set()
  return tasks.filter((t) => {
    const key = String(t?.id || t?.task_id || '')
    if (!key || seen.has(key)) return false
    seen.add(key)
    return true
  })
}

/** Deduplicate resources by id */
export function dedupeResources(resources = []) {
  const seen = new Set()
  return resources.filter((r) => {
    if (!r?.id || seen.has(r.id)) return false
    seen.add(r.id)
    return true
  })
}

/** Filter review plans that belong to current course */
export function scopedReviewPlans(plans = [], currentCourse, validTopicSet) {
  if (!currentCourse?.id) return []
  return plans.filter((item) => {
    const planCourseId = String(item?.courseId || item?.course_id || '')
    const planTopic = String(item?.topic || '')
    if (planCourseId && planCourseId !== String(currentCourse.id)) return false
    if (validTopicSet && validTopicSet.size > 0 && planTopic) {
      if (!validTopicSet.has(planTopic)) return false
    }
    return true
  })
}
