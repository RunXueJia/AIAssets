import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — attach token
http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// Response interceptor — unwrap data & handle errors
http.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body.code && body.code !== 200) {
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body
  },
  async (error) => {
    const config = error.config || {}
    const isRefreshRequest = config.url?.includes('/api/v1/auth/refresh_token')

    if (error.response?.status === 401 && !config.__isRetryRequest && !isRefreshRequest) {
      const auth = useAuthStore()
      try {
        await auth.refreshAccessToken()
        config.__isRetryRequest = true
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${auth.token}`
        return http(config)
      } catch {
        auth.clearAuth()
      }
    }
    const msg = error.response?.data?.message || error.message || '网络错误'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export default http
