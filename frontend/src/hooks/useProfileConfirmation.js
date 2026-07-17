import { useMemo, useState } from 'react'

export function useProfileConfirmation(profileState) {
  const [confirmed, setConfirmed] = useState(false)
  const ready = Boolean(profileState?.ready_for_path_generation)
  const canGenerate = ready && confirmed

  const summary = useMemo(() => ({
    goal: profileState?.profile?.learning_goal || profileState?.course?.goal || '尚未填写',
    level: profileState?.profile?.knowledge_level || '待补充',
    pace: profileState?.profile?.pace_preference || '待补充',
    missing: profileState?.missing_dimensions || [],
  }), [profileState])

  return { ready, confirmed, setConfirmed, canGenerate, summary }
}
