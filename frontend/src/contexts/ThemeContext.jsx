import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const ThemeContext = createContext(null)

const STORAGE_KEY = 'app-theme'

export const THEMES = {
  light: { key: 'light', label: '浅色', icon: 'sun' },
  dark: { key: 'dark', label: '深色', icon: 'moon' },
  system: { key: 'system', label: '跟随系统', icon: 'system' },
}

function resolveTheme(mode) {
  if (mode === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return mode
}

export function ThemeProvider({ children }) {
  const [mode, setMode] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) || 'system'
  })

  // Apply theme to document
  useEffect(() => {
    const resolved = resolveTheme(mode)
    document.documentElement.setAttribute('data-theme', resolved)
    localStorage.setItem(STORAGE_KEY, mode)
  }, [mode])

  // Listen for system theme changes when in system mode
  useEffect(() => {
    if (mode !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      document.documentElement.setAttribute('data-theme', resolveTheme('system'))
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [mode])

  const cycleTheme = useCallback(() => {
    setMode((prev) => {
      const keys = Object.keys(THEMES)
      const idx = keys.indexOf(prev)
      return keys[(idx + 1) % keys.length]
    })
  }, [])

  const resolved = resolveTheme(mode)

  return (
    <ThemeContext.Provider value={{ mode, resolved, cycleTheme, setMode }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
