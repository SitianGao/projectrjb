import { useState, useCallback, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Typography, Divider, Alert, message } from 'antd'
import { UserOutlined, LockOutlined, PhoneOutlined, MessageOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import CharacterGroup from '../components/AnimatedCharacter'

const { Title, Text } = Typography
const MOCK_CODE = '123456'
const CODE_EXPIRE_SEC = 600 // 10分钟

export default function RegisterPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [userNameFocused, setUserNameFocused] = useState(false)
  const [pwFocused, setPwFocused] = useState(false)
  const [codeExpiry, setCodeExpiry] = useState(0) // 剩余秒数
  const timerRef = useRef(null)
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form] = Form.useForm()

  const startCodeTimer = useCallback(() => {
    clearInterval(timerRef.current)
    setCodeExpiry(CODE_EXPIRE_SEC)
    timerRef.current = setInterval(() => {
      setCodeExpiry((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current)
          form.setFieldsValue({ code: '' })
          message.warning('验证码已过期，请重新输入手机号获取')
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [form])

  const handlePhoneChange = useCallback((e) => {
    const phone = e.target.value
    if (/^1[3-9]\d{9}$/.test(phone)) {
      form.setFieldsValue({ code: MOCK_CODE })
      startCodeTimer()
    } else {
      // 手机号不满足时清除验证码
      clearInterval(timerRef.current)
      setCodeExpiry(0)
      form.setFieldsValue({ code: '' })
    }
  }, [form, startCodeTimer])

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${String(s).padStart(2, '0')}`
  }

  const onFinish = async (values) => {
    setError(null)
    setLoading(true)
    try {
      const ok = await register(values.username, values.password, values.phone)
      if (ok) { navigate('/', { replace: true }) }
    } catch (err) {
      setError(err.message || '注册失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-split">
      {/* 左侧：4 个交互角色 */}
      <div className="login-left">
        <div className="login-bg-deco">
          <div className="deco-circle c1" />
          <div className="deco-circle c2" />
          <div className="deco-circle c3" />
          <div className="deco-circle c4" />
        </div>

        <CharacterGroup
          userNameFocused={userNameFocused}
          pwFocused={pwFocused}
        />
      </div>

      {/* 右侧：注册表单 */}
      <div className="login-right">
        <div className="login-form-wrap">
          <div className="auth-header">
            <Title level={3}>📚 创建账号</Title>
            <Text type="secondary">加入智学相伴，开启学习之旅</Text>
          </div>

          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
              style={{ marginBottom: 16, borderRadius: 8 }}
            />
          )}

          <Form form={form} name="register" onFinish={onFinish} size="large" autoComplete="off">
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少 3 位' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
                onFocus={() => setUserNameFocused(true)}
                onBlur={() => setUserNameFocused(false)}
              />
            </Form.Item>

            {/* 手机号 */}
            <Form.Item
              name="phone"
              rules={[
                { required: true, message: '请输入手机号' },
                { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
              ]}
            >
              <Input
                prefix={<PhoneOutlined />}
                placeholder="手机号"
                onChange={handlePhoneChange}
              />
            </Form.Item>

            {/* 验证码（10分钟内有效） */}
            <Form.Item
              name="code"
              rules={[{ required: true, message: '请输入验证码' }]}
            >
              <Input
                prefix={<MessageOutlined />}
                placeholder="请输入您的验证码"
                suffix={
                  codeExpiry > 0 ? (
                    <Text style={{ fontSize: 12, color: '#8b5cf6', whiteSpace: 'nowrap' }}>
                      您的验证码将在 {formatTime(codeExpiry)} 后失效
                    </Text>
                  ) : null
                }
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少 6 位' },
                {
                  validator(_, value) {
                    if (!value) return Promise.resolve()
                    if (!/[a-z]/.test(value)) return Promise.reject(new Error('密码需包含小写字母'))
                    if (!/[A-Z]/.test(value)) return Promise.reject(new Error('密码需包含大写字母'))
                    if (!/[0-9]/.test(value)) return Promise.reject(new Error('密码需包含数字'))
                    if (!/[\p{P}\p{S}]/u.test(value)) return Promise.reject(new Error('密码需包含标点符号'))
                    return Promise.resolve()
                  },
                },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="需包含大小写字母、数字和符号，至少6位"
                onFocus={() => setPwFocused(true)}
                onBlur={() => setPwFocused(false)}
              />
            </Form.Item>

            <Form.Item
              name="confirm"
              dependencies={['password']}
              rules={[
                { required: true, message: '请确认密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) return Promise.resolve()
                    return Promise.reject(new Error('两次密码不一致'))
                  },
                }),
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" block loading={loading}>
                注 册
              </Button>
            </Form.Item>
          </Form>

          <Divider plain>
            <Text type="secondary" style={{ fontSize: 13 }}>已有账号？</Text>
          </Divider>

          <Link to="/login">
            <Button block>去登录</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
