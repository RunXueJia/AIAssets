import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const refreshToken = ref(localStorage.getItem('admin_refresh_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('admin_user') || 'null'))

  const isAuthenticated = computed(() => !!token.value && user.value?.role === 'admin')

  function setAuth(accessToken, refreshTokenVal, userData) {
    token.value = accessToken
    refreshToken.value = refreshTokenVal
    user.value = userData
    localStorage.setItem('admin_token', accessToken)
    localStorage.setItem('admin_refresh_token', refreshTokenVal)
    localStorage.setItem('admin_user', JSON.stringify(userData))
  }

  function clearAuth() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_refresh_token')
    localStorage.removeItem('admin_user')
  }

  async function login(account, password) {
    const res = await authApi.login(account, password, 'admin')
    if (res.data.user.role !== 'admin') {
      throw new Error('该账号无管理员权限')
    }
    setAuth(res.data.access_token, res.data.refresh_token, res.data.user)
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // Ignore server errors on logout
    }
    clearAuth()
    router.replace('/login')
  }

  async function refreshAccessToken() {
    try {
      const res = await authApi.refreshToken(refreshToken.value)
      token.value = res.data.access_token
      refreshToken.value = res.data.refresh_token
      localStorage.setItem('admin_token', res.data.access_token)
      localStorage.setItem('admin_refresh_token', res.data.refresh_token)
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
    setAuth,
    clearAuth,
    login,
    logout,
    refreshAccessToken,
  }
})
