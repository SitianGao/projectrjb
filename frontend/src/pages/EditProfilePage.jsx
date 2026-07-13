import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Typography, Card, Avatar, Divider, message } from 'antd'
import { UserOutlined, MailOutlined, PhoneOutlined, EditOutlined, ArrowLeftOutlined, MessageOutlined, CameraOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'

const { Title, Text } = Typography
const { TextArea } = Input
const MOCK_CODE = '123456'
const CODE_EXPIRE_SEC = 600

export default function EditProfilePage() {
  const [loading, setLoading] = useState(false)
  const [rebinding, setRebinding] = useState(false)
  const [codeExpiry, setCodeExpiry] = useState(0)
  const [avatarPreview, setAvatarPreview] = useState(null) // base64 预览
  const [avatarHover, setAvatarHover] = useState(false)
  const timerRef = useRef(null)
  const fileInputRef = useRef(null)
  const { user, updateProfile } = useAuth()
  const navigate = useNavigate()
  const [form] = Form.useForm()

  // 当前展示的头像：已选未保存 > 已保存的头像
  const displayAvatar = avatarPreview || user?.avatar

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
          form.setFieldsValue({ newPhoneCode: '' })
          message.warning('验证码已过期，请重新获取')
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [form])

  const handleNewPhoneChange = useCallback((e) => {
    const phone = e.target.value
    if (/^1[3-9]\d{9}$/.test(phone)) {
      form.setFieldsValue({ newPhoneCode: MOCK_CODE })
      startCodeTimer()
    } else {
      clearInterval(timerRef.current)
      setCodeExpiry(0)
      form.setFieldsValue({ newPhoneCode: '' })
    }
  }, [form, startCodeTimer])

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${String(s).padStart(2, '0')}`
  }

  const handleAvatarChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      message.error('请选择图片文件')
      return
    }
    if (file.size > 2 * 1024 * 1024) {
      message.error('图片大小不能超过 2MB')
      return
    }
    const reader = new FileReader()
    reader.onload = () => setAvatarPreview(reader.result)
    reader.readAsDataURL(file)
    // 清除 input 以便重复选择同一文件
    e.target.value = ''
  }


  const cancelRebind = () => {
    clearInterval(timerRef.current)
    setCodeExpiry(0)
    setRebinding(false)
    form.resetFields(['newPhone', 'newPhoneCode'])
  }

  const onFinish = async (values) => {
    setLoading(true)
    try {
      const updates = { email: values.email, bio: values.bio }
      // 头像：null 表示删除，base64 表示新头像
      if (avatarPreview !== user?.avatar) {
        updates.avatar = avatarPreview // null = 删除头像
      }
      if (rebinding && values.newPhone) {
        updates.phone = values.newPhone
      }
      const ok = await updateProfile(updates)
      if (ok) {
        clearInterval(timerRef.current)
        navigate(-1)
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
      <div style={{ width: '100%', maxWidth: 560 }}>

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
          <EditOutlined style={{ marginRight: 8, color: '#8b5cf6' }} />
          修改个人信息
        </Title>
        <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
          完善你的个人资料，让学习伙伴更了解你
        </Text>

        <Card
          style={{
            borderRadius: 12,
            border: '1px solid var(--border)',
            background: 'var(--bg-card)',
            boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
          }}
        >
          {/* 头像区 */}
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            {/* 隐藏文件输入 */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleAvatarChange}
              style={{ display: 'none' }}
            />

            {/* 可点击头像 */}
            <div
              style={{
                position: 'relative',
                display: 'inline-block',
                cursor: 'pointer',
              }}
              onClick={() => fileInputRef.current?.click()}
              onMouseEnter={() => setAvatarHover(true)}
              onMouseLeave={() => setAvatarHover(false)}
            >
              <Avatar
                size={80}
                icon={<UserOutlined />}
                src={displayAvatar}
                style={{
                  backgroundColor: '#1677ff',
                  boxShadow: '0 4px 12px rgba(22,119,255,0.3)',
                  opacity: avatarHover ? 0.6 : 1,
                  transition: 'opacity 0.2s',
                }}
              />
              {/* hover 遮罩 */}
              <div style={{
                position: 'absolute',
                top: 0, left: 0, right: 0, bottom: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '50%',
                opacity: avatarHover ? 1 : 0,
                transition: 'opacity 0.2s',
                pointerEvents: 'none',
              }}>
                <CameraOutlined style={{ fontSize: 24, color: '#fff' }} />
              </div>
            </div>

            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                点击头像上传
              </Text>
            </div>
          </div>

          <Divider style={{ margin: '0 0 24px' }} />

          <Form
            form={form}
            layout="vertical"
            onFinish={onFinish}
            initialValues={{
              email: user?.email || '',
              bio: user?.bio || '',
            }}
            size="large"
          >
            <Form.Item
              label="用户名"
              help="用户名不可修改"
            >
              <Input
                value={user?.username}
                disabled
                prefix={<UserOutlined />}
              />
            </Form.Item>

            <Form.Item
              name="email"
              label="邮箱"
              rules={[
                { type: 'email', message: '请输入正确的邮箱格式' },
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="example@mail.com"
              />
            </Form.Item>

            {/* ===== 手机号区域 ===== */}
            {!rebinding ? (
              <div style={{ marginBottom: 24 }}>
                <div style={{ marginBottom: 8 }}>
                  <Text style={{ fontSize: 14 }}>绑定手机号</Text>
                </div>
                <Input
                  prefix={<PhoneOutlined />}
                  value={maskedPhone}
                  disabled
                />
                <Button
                  type="link"
                  onClick={() => setRebinding(true)}
                  style={{ padding: 0, marginTop: 6, fontSize: 13 }}
                >
                  重新绑定手机号
                </Button>
              </div>
            ) : (
              <>
                <div style={{
                  marginBottom: 16,
                  padding: '12px 16px',
                  borderRadius: 8,
                  background: 'var(--surface-secondary)',
                  border: '1px solid var(--border)',
                }}>
                  <Text strong style={{ fontSize: 13, color: '#8b5cf6' }}>重新绑定手机号</Text>
                  <Button
                    type="link"
                    size="small"
                    onClick={cancelRebind}
                    style={{ float: 'right', fontSize: 12, padding: 0 }}
                  >
                    取消
                  </Button>

                  <Form.Item
                    name="newPhone"
                    label="新手机号"
                    style={{ marginTop: 12, marginBottom: 12 }}
                    rules={[
                      { required: true, message: '请输入新手机号' },
                      { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
                    ]}
                  >
                    <Input
                      prefix={<PhoneOutlined />}
                      placeholder="请输入新手机号"
                      onChange={handleNewPhoneChange}
                    />
                  </Form.Item>

                  <Form.Item
                    name="newPhoneCode"
                    label="验证码"
                    style={{ marginBottom: 0 }}
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
                </div>
              </>
            )}

            <Form.Item
              name="bio"
              label="个人简介"
              rules={[
                { max: 200, message: '简介不超过 200 个字符' },
              ]}
            >
              <TextArea
                rows={3}
                placeholder="介绍一下自己，比如学习目标、感兴趣的领域..."
                style={{ borderRadius: 6 }}
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
                保存修改
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </div>
    </div>
  )
}
