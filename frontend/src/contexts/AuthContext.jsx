import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { message } from 'antd'
import client from '../api/client'

const AuthContext = createContext(null)
const USER_STORAGE_KEY = 'auth_user'
const TOKEN_STORAGE_KEY = 'auth_token'

function readStoredUser() {
  try {
    if (!localStorage.getItem(TOKEN_STORAGE_KEY)) return null
    const saved = localStorage.getItem(USER_STORAGE_KEY)
    return saved ? JSON.parse(saved) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser)

  const saveUser = useCallback((nextUser) => {
    setUser(nextUser)
    if (nextUser) localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(nextUser))
    else localStorage.removeItem(USER_STORAGE_KEY)
  }, [])

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!token) return
    client.get('/auth/me').then(saveUser).catch(() => {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      saveUser(null)
    })
  }, [saveUser])

  const acceptSession = useCallback((session) => {
    localStorage.setItem(TOKEN_STORAGE_KEY, session.token)
    saveUser(session.user)
  }, [saveUser])

  const login = useCallback(async (username, password) => {
    try {
      const session = await client.post('/auth/login', { username, password })
      acceptSession(session)
      message.success(`欢迎回来，${session.user.name || session.user.username} 同学`)
      return true
    } catch (error) {
      message.error(error.message || '用户名或密码错误')
      return false
    }
  }, [acceptSession])

  const register = useCallback(async (username, password, phone) => {
    try {
      const session = await client.post('/auth/register', { username, password, phone })
      acceptSession(session)
      message.success('注册成功，已创建独立课程空间')
      return true
    } catch (error) {
      message.error(error.message || '注册失败')
      return false
    }
  }, [acceptSession])

  const updateProfile = useCallback(async (updates) => {
    const updated = await client.put('/auth/profile', updates)
    saveUser(updated)
    message.success('个人信息已更新')
    return true
  }, [saveUser])

  const changePassword = useCallback(async (oldPassword, newPassword) => {
    await client.put('/auth/password', { old_password: oldPassword, new_password: newPassword })
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    saveUser(null)
    message.success('密码修改成功，请重新登录')
    return true
  }, [saveUser])

  const resetPasswordByPhone = useCallback(async () => {
    message.error('短信验证服务尚未配置，比赛版本不使用模拟验证码')
    return false
  }, [])

  const createCourse = useCallback(async (title, goal = '') => {
    const updated = await client.post('/auth/courses', { title, goal })
    saveUser(updated)
    return updated.active_course
  }, [saveUser])

  const activateCourse = useCallback(async (courseId) => {
    const updated = await client.post(`/auth/courses/${courseId}/activate`)
    saveUser(updated)
    return updated.active_course
  }, [saveUser])

  const updateCourse = useCallback(async (courseId, updates) => {
    const updated = await client.put(`/auth/courses/${courseId}`, updates)
    saveUser(updated)
    return updated.active_course
  }, [saveUser])

  const refreshCourses = useCallback(async () => {
    const updated = await client.get('/auth/courses')
    saveUser(updated)
    return updated.courses || []
  }, [saveUser])

  const logout = useCallback(async () => {
    try {
      await client.post('/auth/logout')
    } catch {
      // 本地令牌仍需清理。
    }
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    saveUser(null)
    message.success('已退出登录')
  }, [saveUser])

  return (
    <AuthContext.Provider value={{
      user,
      studentId: user?.student_id || null,
      courses: user?.courses || [],
      activeCourse: user?.active_course || null,
      login,
      register,
      updateProfile,
      changePassword,
      resetPasswordByPhone,
      createCourse,
      activateCourse,
      updateCourse,
      refreshCourses,
      logout,
      isLoggedIn: !!user,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
