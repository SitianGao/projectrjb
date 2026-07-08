import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { message } from 'antd'
import client from '../api/client'

const AuthContext = createContext(null)

const STORAGE_KEY = 'auth_user'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  useEffect(() => {
    if (user) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [user])

  const login = useCallback(async (username, password) => {
    try {
      const data = await client.post('/auth/login', { username, password })
      const { token, ...userInfo } = data
      if (token) localStorage.setItem('auth_token', token)
      setUser(userInfo)
      message.success(`欢迎回来，${userInfo.name || username}`)
      return true
    } catch (err) {
      message.error(err.message || '登录失败')
      return false
    }
  }, [])

  const register = useCallback(async (username, password, name, email) => {
    try {
      const data = await client.post('/auth/register', { username, password, name, email })
      const { token, ...userInfo } = data
      if (token) localStorage.setItem('auth_token', token)
      setUser(userInfo)
      message.success('注册成功')
      return true
    } catch (err) {
      message.error(err.message || '注册失败')
      return false
    }
  }, [])

  const logout = useCallback(() => {
    setUser(null)
    message.success('已退出登录')
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isLoggedIn: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
