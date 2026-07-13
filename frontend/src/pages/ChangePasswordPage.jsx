import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Typography, Card, Divider } from 'antd'
import { LockOutlined, ArrowLeftOutlined, KeyOutlined, PhoneOutlined, MessageOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'

const { Title, Text } = Typography
const MOCK_CODE = '123456'
const CODE_EXPIRE_SEC = 600 // 10分钟

export default function ChangePasswordPage() {
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState('password') // 'password' | 'sms'
  const [codeExpiry, setCodeExpiry] = useState(0)
  const [codeSent, setCodeSent] = useState(false)
  const timerRef = useRef(null)
  const { user, changePassword, resetPasswordByPhone } = useAuth()
  const navigate = useNavigate()
  const [form] = Form.useForm()

  // 手机号脱敏显示
  const maskedPhone = user?.phone
    ? user.phone.slice(0, 3) + '****' + user.phone.slice(-4)
    : '未绑定手机号'

  const startCodeTimer = useCallback(() => {
    clearInterval(timerRef.current)
    setCodeExpiry(CODE_EXPIRE_SEC)
    timerRef.current = setInterval(() => {
      setCodeExpiry((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current)
          form.setFieldsValue({ code: '' })
          setCodeSent(false)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [form])

  const handleSendCode = useCallback(() => {
    if (!user?.phone) return
    form.setFieldsValue({ code: MOCK_CODE })
    setCodeSent(true)
    startCodeTimer()
  }, [user, form, startCodeTimer])

  const handleModeSwitch = (nextMode) => {
    clearInterval(timerRef.current)
    setCodeExpiry(0)
    setCodeSent(false)
    setMode(nextMode)
    form.resetFields()
  }

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${String(s).padStart(2, '0')}`
  }

  const onFinish = async (values) => {
    setLoading(true)
    try {
      let ok
      if (mode === 'password') {
        ok = await changePassword(values.oldPassword, values.newPassword)
      } else {
        ok = await resetPasswordByPhone(user.phone, values.code, values.newPassword)
      }
      if (ok) {
        navigate('/login', { replace: true })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-page)',
      display: 'flex',
      justifyContent: 'center',
      padding: '40px 24px',
    }}>
      <div style={{ width: '100%', maxWidth: 500 }}>

        {/* 返回按钮 */}
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(-1)}
          style={{ marginBottom: 16, color: 'var(--text-secondary)' }}
        >
          返回
        </Button>

        <Title level={3} style={{ marginBottom: 4 }}>
          <KeyOutlined style={{ marginRight: 8, color: '#8b5cf6' }} />
          修改密码
        </Title>
        <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
          为保障账号安全，请设置强密码
        </Text>

        <Card
          style={{
            borderRadius: 12,
            border: '1px solid var(--border)',
            background: 'var(--bg-card)',
            boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
          }}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={onFinish}
            size="large"
          >
            {/* ===== 模式切换按钮 ===== */}
            <div style={{ display: 'flex', marginBottom: 20, background: 'var(--surface-secondary)', borderRadius: 8, padding: 4 }}>
              <div
                onClick={() => handleModeSwitch('password')}
                style={{
                  flex: 1, textAlign: 'center', padding: '8px 0', borderRadius: 6,
                  cursor: 'pointer', fontSize: 14, fontWeight: mode === 'password' ? 600 : 400,
                  background: mode === 'password' ? 'var(--bg-card)' : 'transparent',
                  color: mode === 'password' ? '#8b5cf6' : 'var(--text-secondary)',
                  boxShadow: mode === 'password' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                  transition: 'all 0.2s',
                }}
              >
                原密码修改
              </div>
              <div
                onClick={() => handleModeSwitch('sms')}
                style={{
                  flex: 1, textAlign: 'center', padding: '8px 0', borderRadius: 6,
                  cursor: 'pointer', fontSize: 14, fontWeight: mode === 'sms' ? 600 : 400,
                  background: mode === 'sms' ? 'var(--bg-card)' : 'transparent',
                  color: mode === 'sms' ? '#8b5cf6' : 'var(--text-secondary)',
                  boxShadow: mode === 'sms' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                  transition: 'all 0.2s',
                }}
              >
                手机验证
              </div>
            </div>

            {/* ===== 原密码模式 ===== */}
            {mode === 'password' && (
              <Form.Item
                name="oldPassword"
                label="原密码"
                rules={[{ required: true, message: '请输入原密码' }]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="请输入当前密码"
                />
              </Form.Item>
            )}

            {/* ===== 手机验证模式 ===== */}
            {mode === 'sms' && (
              <>
                {/* 手机号展示 */}
                <Form.Item label="绑定手机号">
                  <Input
                    prefix={<PhoneOutlined />}
                    value={maskedPhone}
                    disabled
                  />
                </Form.Item>

                {/* 验证码 */}
                <Form.Item
                  name="code"
                  label="短信验证码"
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

                {/* 发送验证码按钮 */}
                {!codeSent && (
                  <div style={{ marginBottom: 16, marginTop: -8 }}>
                    <Button
                      type="link"
                      onClick={handleSendCode}
                      disabled={!user?.phone}
                      style={{ padding: 0, fontSize: 13 }}
                    >
                      {user?.phone ? '点击获取验证码' : '请先在个人设置中绑定手机号'}
                    </Button>
                  </div>
                )}
                {codeSent && (
                  <div style={{ marginBottom: 16, marginTop: -8 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      ✓ 验证码已发送至 {maskedPhone}
                    </Text>
                  </div>
                )}
              </>
            )}

            <Divider style={{ margin: '0 0 16px' }} />

            {/* ===== 新密码（两种模式共用） ===== */}
            <Form.Item
              name="newPassword"
              label="新密码"
              rules={[
                { required: true, message: '请输入新密码' },
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
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              label="确认新密码"
              dependencies={['newPassword']}
              rules={[
                { required: true, message: '请再次输入新密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('newPassword') === value) return Promise.resolve()
                    return Promise.reject(new Error('两次密码不一致'))
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请再次输入新密码"
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
              <Button
                type="primary"
                htmlType="submit"
                block
                loading={loading}
                style={{ height: 44, borderRadius: 8, fontSize: 15 }}
              >
                确认修改
              </Button>
            </Form.Item>
          </Form>
        </Card>

        <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginTop: 16, fontSize: 12 }}>
          修改成功后需要重新登录
        </Text>
      </div>
    </div>
  )
}
