import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const ThemeContext = createContext(null)

const STORAGE_KEY = 'app-theme'

export const THEMES = {
  light: { key: 'light', label: '浅色', icon: 'sun' },
  dark: { key: 'dark', label: '深色', icon: 'moon' },
  auto: { key: 'auto', label: '跟随系统', icon: 'desktop' },
}

/** 获取系统当前主题偏好 */
function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/** 首次加载时读取存储的模式 */
function getInitialMode() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'auto') return stored
  // 无存储记录 → 默认跟随系统
  return 'auto'
}

export function ThemeProvider({ children }) {
  const [mode, setModeState] = useState(getInitialMode)
  // resolved 始终为实际渲染的主题：auto 模式下跟随系统
  const [systemTheme, setSystemTheme] = useState(getSystemTheme)

  // 监听系统主题变化
  useEffect(() => {
    const mql = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e) => setSystemTheme(e.matches ? 'dark' : 'light')
    mql.addEventListener('change', handler)
    return () => mql.removeEventListener('change', handler)
  }, [])

  // 应用到 document 并持久化
  useEffect(() => {
    const resolved = mode === 'auto' ? systemTheme : mode
    document.documentElement.setAttribute('data-theme', resolved)
    localStorage.setItem(STORAGE_KEY, mode)
  }, [mode, systemTheme])

  const setMode = useCallback((next) => {
    setModeState(next)
  }, [])

  const cycleTheme = useCallback(() => {
    setModeState((prev) => {
      const keys = Object.keys(THEMES)
      const idx = keys.indexOf(prev)
      return keys[(idx + 1) % keys.length]
    })
  }, [])

  // resolved: 实际生效的主题（light / dark）
  const resolved = mode === 'auto' ? systemTheme : mode

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
