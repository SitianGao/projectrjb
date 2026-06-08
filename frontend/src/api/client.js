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
    // 如需 token，从这里注入
    // const token = localStorage.getItem('token')
    // if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：统一错误处理
client.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      const msg = data?.detail || data?.message || `请求失败 (${status})`

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
          // 参数校验错误，取出第一条
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
      message.error('请求配置错误')
    }

    return Promise.reject(error)
  },
)

export default client
