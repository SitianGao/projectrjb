import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Typography, Divider, Steps, message } from 'antd'
import { LockOutlined, MailOutlined, NumberOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import CharacterGroup from '../components/AnimatedCharacter'

const { Title, Text } = Typography

// 模拟已注册用户邮箱
const REGISTERED_EMAILS = ['admin@example.com', 'student@example.com']

export default function ForgotPasswordPage() {
  const [step, setStep] = useState(0)            // 0=输入邮箱, 1=输入验证码+新密码
  const [email, setEmail] = useState('')
  const [emailFocused, setEmailFocused] = useState(false)
  const [pwFocused, setPwFocused] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  // Step 0：发送验证码
  const onSendCode = async (values) => {
    setLoading(true)
    // 模拟请求
    await new Promise((r) => setTimeout(r, 800))

    if (!REGISTERED_EMAILS.includes(values.email)) {
      message.error('该邮箱未注册')
      setLoading(false)
      return
    }

    setEmail(values.email)
    message.success('验证码已发送至您的邮箱（模拟码：6666）')
    setLoading(false)
    setStep(1)
  }

  // Step 1：重置密码
  const onReset = async (values) => {
    setLoading(true)
    await new Promise((r) => setTimeout(r, 800))

    if (values.code !== '6666') {
      message.error('验证码错误')
      setLoading(false)
      return
    }

    message.success('密码重置成功，请重新登录')
    setLoading(false)
    navigate('/login', { replace: true })
  }

  const steps = [
    { title: '验证身份' },
    { title: '重置密码' },
  ]

  return (
    <div className="login-split">
      {/* 左侧：交互角色 */}
      <div className="login-left">
        <div className="login-bg-deco">
          <div className="deco-circle c1" />
          <div className="deco-circle c2" />
          <div className="deco-circle c3" />
          <div className="deco-circle c4" />
        </div>

        <CharacterGroup
          userNameFocused={emailFocused}
          pwFocused={pwFocused}
        />
      </div>

      {/* 右侧：忘记密码表单 */}
      <div className="login-right">
        <div className="login-form-wrap">
          <div className="auth-header">
            <Title level={3}>🔑 找回密码</Title>
            <Text type="secondary">{step === 0 ? '请输入注册邮箱，获取验证码' : '请输入验证码和新密码'}</Text>
          </div>

          <Steps
            current={step}
            items={steps}
            size="small"
            style={{ marginBottom: 32 }}
          />

          {step === 0 && (
            <Form name="forgot" onFinish={onSendCode} size="large" autoComplete="off">
              <Form.Item
                name="email"
                rules={[
                  { required: true, message: '请输入注册邮箱' },
                  { type: 'email', message: '邮箱格式不正确' },
                ]}
              >
                <Input
                  prefix={<MailOutlined />}
                  placeholder="注册邮箱"
                  onFocus={() => setEmailFocused(true)}
                  onBlur={() => setEmailFocused(false)}
                />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" block loading={loading}>
                  发送验证码
                </Button>
              </Form.Item>
            </Form>
          )}

          {step === 1 && (
            <Form name="reset" onFinish={onReset} size="large" autoComplete="off">
              <Form.Item
                name="code"
                rules={[
                  { required: true, message: '请输入验证码' },
                  { len: 4, message: '验证码为 4 位数字' },
                ]}
              >
                <Input
                  prefix={<NumberOutlined />}
                  placeholder="验证码（模拟码：6666）"
                  maxLength={4}
                  onFocus={() => setEmailFocused(true)}
                  onBlur={() => setEmailFocused(false)}
                />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[
                  { required: true, message: '请输入新密码' },
                  { min: 6, message: '密码至少 6 位' },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="新密码"
                  onFocus={() => setPwFocused(true)}
                  onBlur={() => setPwFocused(false)}
                />
              </Form.Item>

              <Form.Item
                name="confirm"
                dependencies={['password']}
                rules={[
                  { required: true, message: '请确认新密码' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('password') === value) return Promise.resolve()
                      return Promise.reject(new Error('两次密码不一致'))
                    },
                  }),
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="确认新密码"
                />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" block loading={loading}>
                  重置密码
                </Button>
              </Form.Item>
            </Form>
          )}

          <Divider plain>
            <Text type="secondary" style={{ fontSize: 13 }}>想起密码了？</Text>
          </Divider>

          <Link to="/login">
            <Button block icon={<ArrowLeftOutlined />}>返回登录</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
