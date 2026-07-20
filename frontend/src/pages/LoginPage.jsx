import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Typography, Divider, Alert } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import { getSessionBootstrap, resolveLoginTarget } from '../services/sessionService'
import CharacterGroup from '../components/AnimatedCharacter'

const { Title, Text } = Typography

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [userNameFocused, setUserNameFocused] = useState(false)
  const [pwFocused, setPwFocused] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const onFinish = async (values) => {
    setError(null)
    setLoading(true)
    try {
      const ok = await login(values.username, values.password)
      if (ok) {
        const bootstrap = await getSessionBootstrap().catch(() => null)
        navigate(resolveLoginTarget(bootstrap), { replace: true })
      }
    } catch (err) {
      setError(err.message || '登录失败，请重试')
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

      {/* 右侧：登录表单 */}
      <div className="login-right">
        <div className="login-form-wrap">
          <div className="auth-header">
            <Title level={3}>📚 智学相伴</Title>
            <Text type="secondary">欢迎回来，请登录您的账号</Text>
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

          <Form name="login" onFinish={onFinish} size="large" autoComplete="off">
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
                onFocus={() => setUserNameFocused(true)}
                onBlur={() => setUserNameFocused(false)}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                onFocus={() => setPwFocused(true)}
                onBlur={() => setPwFocused(false)}
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 12 }}>
              <div style={{ textAlign: 'right' }}>
                <Link
                  to="/forgot-password"
                  style={{ fontSize: 13, color: '#8b5cf6' }}
                >
                  忘记密码？
                </Link>
              </div>
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" block loading={loading}>
                登 录
              </Button>
            </Form.Item>
          </Form>

          <Divider plain>
            <Text type="secondary" style={{ fontSize: 13 }}>还没有账号？</Text>
          </Divider>

          <Link to="/register">
            <Button block>注 册</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
