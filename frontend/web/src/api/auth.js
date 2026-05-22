import http from '@/utils/http'

export const authApi = {
  login(account, password, clientType = 'web') {
    return http.post('/api/v1/auth/login', { account, password, client_type: clientType })
  },
  register(data) {
    return http.post('/api/v1/auth/register', data)
  },
  guestSession(clientId) {
    return http.post('/api/v1/auth/guest_session', { client_id: clientId })
  },
  refreshToken(token) {
    return http.post('/api/v1/auth/refresh_token', { refresh_token: token })
  },
  logout() {
    return http.post('/api/v1/auth/logout')
  },
}
