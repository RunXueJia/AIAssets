import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)
  const isGuest = computed(() => user.value?.role === 'guest')
  const isLoggedIn = computed(() => user.value && user.value.role !== 'guest')

  function setAuth(accessToken, refreshTokenVal, userData) {
    token.value = accessToken
    refreshToken.value = refreshTokenVal
    user.value = userData
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshTokenVal)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  function clearAuth() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  async function initGuestSession() {
    try {
      let clientId = localStorage.getItem('client_id')
      if (!clientId) {
        clientId = crypto.randomUUID()
        localStorage.setItem('client_id', clientId)
      }
      const res = await authApi.guestSession(clientId)
      setAuth(res.data.access_token, res.data.refresh_token, res.data.user)
    } catch {
      // Silent fail — user can still browse but not generate
    }
  }

  async function login(account, password) {
    const res = await authApi.login(account, password, 'web')
    setAuth(res.data.access_token, res.data.refresh_token, res.data.user)
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // Ignore server errors on logout
    }
    clearAuth()
    router.replace('/')
  }

  async function refreshAccessToken() {
    try {
      const res = await authApi.refreshToken(refreshToken.value)
      token.value = res.data.access_token
      refreshToken.value = res.data.refresh_token
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
    } catch {
      clearAuth()
      router.replace('/login')
    }
  }

  return {
    token,
    refreshToken,
    user,
    isAuthenticated,
    isGuest,
    isLoggedIn,
    setAuth,
    clearAuth,
    initGuestSession,
    login,
    logout,
    refreshAccessToken,
  }
})
