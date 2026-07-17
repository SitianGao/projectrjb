import { useCallback } from 'react'

export function useAgentJobEvents(applyEvent) {
  return useCallback((event) => {
    applyEvent?.(event)
  }, [applyEvent])
}
