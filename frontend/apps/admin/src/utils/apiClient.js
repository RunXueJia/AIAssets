import axios from 'axios'

const TOKEN_KEY = 'hours24_access_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
    return
  }
  localStorage.removeItem(TOKEN_KEY)
}

export function createApiClient(options = {}) {
  const client = axios.create({
    baseURL: options.baseURL || import.meta.env.VITE_API_BASE_URL || '/api/v1',
    timeout: 20000
  })

  client.interceptors.request.use((config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  client.interceptors.response.use(
    (response) => {
      const body = response.data
      if (body && typeof body === 'object' && 'code' in body) {
        if (body.code !== 200) {
          const error = new Error(body.message || 'Request failed')
          error.responseBody = body
          throw error
        }
        return body.data
      }
      return body
    },
    (error) => {
      if (error.response?.status === 401) {
        setToken('')
        window.dispatchEvent(new CustomEvent('hours24:unauthorized'))
      }

      throw error
    }
  )

  return client
}

export const apiClient = createApiClient()
