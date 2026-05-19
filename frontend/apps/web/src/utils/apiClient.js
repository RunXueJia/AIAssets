import axios from 'axios'

export function createApiClient(options = {}) {
  const client = axios.create({
    baseURL: options.baseURL || import.meta.env.VITE_API_BASE_URL || '/api/v1',
    timeout: 20000
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
      throw error
    }
  )

  return client
}

export const apiClient = createApiClient()
