import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Typography, Divider, Alert } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined, IdcardOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import CharacterGroup from '../components/AnimatedCharacter'

const { Title, Text } = Typography

export default function RegisterPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [userNameFocused, setUserNameFocused] = useState(false)
  const [pwFocused, setPwFocused] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const onFinish = async (values) => {
    setError(null)
    setLoading(true)
    try {
      const ok = await register(values.username, values.password, values.name, values.email)
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
            <Text type="secondary">加入智能学习平台，开启学习之旅</Text>
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

          <Form name="register" onFinish={onFinish} size="large" autoComplete="off">
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

            <Form.Item
              name="name"
              rules={[{ required: true, message: '请输入姓名' }]}
            >
              <Input prefix={<IdcardOutlined />} placeholder="姓名" />
            </Form.Item>

            <Form.Item
              name="email"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '邮箱格式不正确' },
              ]}
            >
              <Input prefix={<MailOutlined />} placeholder="邮箱" />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少 6 位' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
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
