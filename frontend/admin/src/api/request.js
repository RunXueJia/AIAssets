import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const ERROR_MESSAGES = {
  40001: '参数不完整，请检查后重试',
  40100: '未登录或登录已过期，请重新登录',
  40300: '当前账号无权限操作',
  40400: '数据不存在或已被删除',
  40900: '当前状态不允许此操作',
  42900: '请求过于频繁，请稍后重试',
  50000: '服务异常，请稍后重试',
  50200: '外部服务异常，请稍后重试',
}

function isAuthUrl(url) {
  return url === '/auth/login' || url === '/auth/logout'
}

function handle401() {
  const auth = useAuthStore()
  auth.logout()
  router.push('/login')
}

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

axiosInstance.interceptors.request.use(
  (config) => {
    const auth = useAuthStore()
    if (auth.token) {
      config.headers.Authorization = `Bearer ${auth.token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

axiosInstance.interceptors.response.use(
  (response) => {
    const { data, config } = response
    if (data.code !== undefined && data.code !== 0) {
      // 401 on login page = wrong credentials, not expired token
      if (data.code === 40100 && !isAuthUrl(config.url)) {
        handle401()
        return Promise.reject(new Error('未登录或登录已过期'))
      }
      const message = ERROR_MESSAGES[data.code] || data.message || '请求失败'
      ElMessage.error(message)
      return Promise.reject(new Error(message))
    }
    return data
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      const url = error.response.config?.url || ''
      if (status === 401 && !isAuthUrl(url)) {
        handle401()
        ElMessage.error('未登录或登录已过期，请重新登录')
      } else if (status === 403) {
        ElMessage.error('当前账号无权限操作')
      } else if (status >= 500) {
        ElMessage.error('服务异常，请稍后重试')
      } else {
        const msg = error.response.data?.message || '请求失败'
        ElMessage.error(msg)
      }
    } else if (error.message) {
      if (!error.message.includes('未登录')) {
        ElMessage.error('网络异常，请检查连接后重试')
      }
    }
    return Promise.reject(error)
  },
)

// ---- Mock adapter ----
const mockHandlers = {}

function matchMockHandler(method, url) {
  const key = `${method.toUpperCase()}:${url.split('?')[0]}`
  let handler = mockHandlers[key]
  if (handler) return handler

  for (const [pattern, fn] of Object.entries(mockHandlers)) {
    const [pMethod, pUrl] = pattern.split(':')
    if (pMethod !== method.toUpperCase()) continue
    const regex = new RegExp('^' + pUrl.replace(/\{[^}]+\}/g, '([^/]+)') + '$')
    const match = key.split(':')[1].match(regex)
    if (match) {
      return (data) => fn(data, ...match.slice(1))
    }
  }
  return null
}

function handleMockResponse(res, url) {
  if (res.code !== undefined && res.code !== 0) {
    if (res.code === 40100 && !isAuthUrl(url)) {
      handle401()
      return Promise.reject(new Error('未登录或登录已过期'))
    }
    const message = ERROR_MESSAGES[res.code] || res.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(new Error(message))
  }
  return res
}

async function mockRequest(method, url, data) {
  const handler = matchMockHandler(method, url)
  if (!handler) {
    console.warn(`[Mock] No handler for ${method}:${url}`)
    return { code: 0, message: 'success', data: null }
  }
  const auth = useAuthStore()
  if (!isAuthUrl(url) && !auth.token) {
    return handleMockResponse({ code: 40100, message: '未登录或 Token 过期', data: null }, url)
  }
  await new Promise((r) => setTimeout(r, 200 + Math.random() * 400))
  const result = await handler(data)
  return handleMockResponse(result, url)
}

// ---- Public API ----

function request(config) {
  if (USE_MOCK) {
    const method = (config.method || 'get').toUpperCase()
    const url = config.url
    const data = config.data || config.params
    return mockRequest(method, url, data)
  }
  return axiosInstance(config)
}

request.registerMock = function (handlers) {
  Object.assign(mockHandlers, handlers)
}

request.get = (url, params) => request({ method: 'get', url, params })
request.post = (url, data) => request({ method: 'post', url, data })
request.put = (url, data) => request({ method: 'put', url, data })
request.delete = (url, params) => request({ method: 'delete', url, params })

export default request
