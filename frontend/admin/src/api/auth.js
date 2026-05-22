import http from '@/utils/http'

export const authApi = {
  login(account, password, clientType = 'admin') {
    return http.post('/api/v1/auth/login', { account, password, client_type: clientType })
  },
  logout() {
    return http.post('/api/v1/auth/logout')
  },
  refreshToken(token) {
    return http.post('/api/v1/auth/refresh_token', { refresh_token: token })
  },
  me() {
    return http.get('/api/v1/auth/me')
  },
}
