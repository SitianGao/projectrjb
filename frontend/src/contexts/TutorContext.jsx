import { createContext, useContext, useState, useCallback } from 'react'

const TutorContext = createContext({
  context: {},
  setTutorContext: () => {},
})

export function TutorProvider({ children }) {
  const [context, setContext] = useState({})
  const setTutorContext = useCallback((ctx) => setContext((prev) => ({ ...prev, ...ctx })), [])
  return (
    <TutorContext.Provider value={{ context, setTutorContext }}>
      {children}
    </TutorContext.Provider>
  )
}

export function useTutorContext() {
  return useContext(TutorContext)
}
