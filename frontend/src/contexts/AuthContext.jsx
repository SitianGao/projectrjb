import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { message } from 'antd'
import client from '../api/client'

const AuthContext = createContext(null)

// 模拟用户数据（后续替换为真实 API）
const MOCK_USERS = [
  { id: 1, username: 'admin', password: 'admin123', name: '管理员', email: 'admin@example.com', avatar: null },
  { id: 2, username: 'student', password: 'student123', name: '张同学', email: 'student@example.com', avatar: null },
]

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
    // 模拟登录 —— 后续替换为 client.post('/auth/login', { username, password })
    const found = MOCK_USERS.find(
      (u) => u.username === username && u.password === password,
    )
    if (!found) {
      message.error('用户名或密码错误')
      return false
    }
    const { password: _, ...userInfo } = found
    setUser(userInfo)
    message.success(`欢迎回来，${userInfo.name}`)
    return true
  }, [])

  const register = useCallback(async (username, password, name, email) => {
    // 模拟注册 —— 后续替换为 client.post('/auth/register', { username, password, name, email })
    const exists = MOCK_USERS.find((u) => u.username === username)
    if (exists) {
      message.error('用户名已存在')
      return false
    }
    const newUser = { id: MOCK_USERS.length + 1, username, name, email, avatar: null }
    MOCK_USERS.push({ ...newUser, password })
    setUser(newUser)
    message.success('注册成功')
    return true
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
