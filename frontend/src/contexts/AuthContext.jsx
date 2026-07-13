import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { message } from 'antd'
import client from '../api/client'

const AuthContext = createContext(null)

// 模拟用户数据（后续替换为真实 API）
const MOCK_USERS = [
  {
    id: 1,
    username: 'admin',
    password: 'admin123',
    name: '管理员',
    email: 'admin@example.com',
    phone: '13800138000',
    bio: '平台管理员，热爱教育技术',
    avatar: null,
  },
  {
    id: 2,
    username: 'student',
    password: 'student123',
    name: '小明',
    email: 'student@example.com',
    phone: '13900139000',
    bio: '一名正在努力学习的同学',
    avatar: null,
  },
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
    message.success(`欢迎回来，${userInfo.name || userInfo.username} 同学`)
    return true
  }, [])

  const register = useCallback(async (username, password, phone) => {
    // 模拟注册 —— 后续替换为 client.post('/auth/register', { username, password, phone })
    const exists = MOCK_USERS.find((u) => u.username === username)
    if (exists) {
      message.error('用户名已存在')
      return false
    }
    const newUser = {
      id: MOCK_USERS.length + 1,
      username,
      name: username,
      email: '',
      phone: phone || '',
      bio: '',
      avatar: null,
    }
    MOCK_USERS.push({ ...newUser, password })
    setUser(newUser)
    message.success('注册成功')
    return true
  }, [])

  const updateProfile = useCallback(async (updates) => {
    // 模拟更新 —— 后续替换为 client.put('/auth/profile', updates)
    const mockUser = MOCK_USERS.find((u) => u.id === user?.id)
    if (mockUser) {
      Object.assign(mockUser, updates)
    }
    setUser((prev) => ({ ...prev, ...updates }))
    message.success('个人信息已更新')
    return true
  }, [user])

  const changePassword = useCallback(async (oldPassword, newPassword) => {
    // 模拟改密 —— 后续替换为 client.put('/auth/password', { oldPassword, newPassword })
    const mockUser = MOCK_USERS.find((u) => u.id === user?.id)
    if (!mockUser) {
      message.error('用户不存在')
      return false
    }
    if (mockUser.password !== oldPassword) {
      message.error('原密码不正确')
      return false
    }
    mockUser.password = newPassword
    message.success('密码修改成功，请重新登录')
    setUser(null)
    return true
  }, [user])

  const resetPasswordByPhone = useCallback(async (phone, code, newPassword) => {
    // 模拟手机验证码重置密码 —— 后续替换为真实 API
    const MOCK_CODE = '123456'
    const mockUser = MOCK_USERS.find((u) => u.id === user?.id)
    if (!mockUser) {
      message.error('用户不存在')
      return false
    }
    if (mockUser.phone !== phone) {
      message.error('手机号与绑定号码不一致')
      return false
    }
    if (code !== MOCK_CODE) {
      message.error('验证码错误')
      return false
    }
    mockUser.password = newPassword
    message.success('密码重置成功，请重新登录')
    setUser(null)
    return true
  }, [user])

  const logout = useCallback(() => {
    setUser(null)
    message.success('已退出登录')
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, register, updateProfile, changePassword, resetPasswordByPhone, logout, isLoggedIn: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
