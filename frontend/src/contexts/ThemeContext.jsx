import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const ThemeContext = createContext(null)

const STORAGE_KEY = 'app-theme'

export const THEMES = {
  light: { key: 'light', label: '浅色', icon: 'sun' },
  dark: { key: 'dark', label: '深色', icon: 'moon' },
}

/** 首次加载时自动检测系统主题偏好 */
function getInitialMode() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') return stored
  // 无存储记录 → 跟随系统
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({ children }) {
  const [mode, setMode] = useState(getInitialMode)

  // Apply theme to document & persist
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode)
    localStorage.setItem(STORAGE_KEY, mode)
  }, [mode])

  const cycleTheme = useCallback(() => {
    setMode((prev) => {
      const keys = Object.keys(THEMES)
      const idx = keys.indexOf(prev)
      return keys[(idx + 1) % keys.length]
    })
  }, [])

  // mode 始终为 'light' | 'dark'，resolved 与 mode 一致
  const resolved = mode

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
