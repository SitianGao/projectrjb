import axios from 'axios'
import { message } from 'antd'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：统一解包 + 错误处理
client.interceptors.response.use(
  (response) => {
    const body = response.data

    // 新 API 合同：{ success: true, data: ..., message: "ok" }
    if (body && typeof body === 'object' && 'success' in body) {
      if (body.success === true) {
        return body.data  // 业务层直接拿到 data
      }
      // success === false：业务错误
      const err = new Error(body.message || '请求失败')
      err._businessError = true
      err.code = body.code
      return Promise.reject(err)
    }

    // 旧格式 / 非标准响应：原样返回
    return body
  },
  (error) => {
    // 业务异常直接透传，由调用方自行处理
    if (error._businessError) {
      return Promise.reject(error)
    }

    if (error.response) {
      const { status, data, config } = error.response
      const msg = data?.detail || data?.message || `请求失败 (${status})`
      error.code = data?.code || error.code
      error.status = status
      error.requestUrl = `${config?.baseURL || ''}${config?.url || ''}`
      error.message = msg

      switch (status) {
        case 401:
          message.error('未登录或登录已过期')
          break
        case 403:
          message.error('没有访问权限')
          break
        case 404:
          message.error('请求的资源不存在')
          break
        case 422:
          if (data?.detail && Array.isArray(data.detail)) {
            message.error(data.detail[0]?.msg || msg)
          } else {
            message.error(msg)
          }
          break
        case 500:
          message.error('服务器内部错误')
          break
        default:
          message.error(msg)
      }
    } else if (error.request) {
      message.error('网络连接失败，请检查网络')
    } else {
      message.error(error.message || '请求失败')
    }

    return Promise.reject(error)
  },
)

export default client
