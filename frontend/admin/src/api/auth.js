import request from './request'

export function login(username, password) {
  return request.post('/auth/login', { username, password }).then((r) => r.data)
}

export function logout() {
  return request.post('/auth/logout', {}).then((r) => r.data)
}

export function getMe() {
  return request.get('/auth/me').then((r) => r.data)
}
