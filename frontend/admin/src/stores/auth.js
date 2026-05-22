import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const refreshToken = ref(localStorage.getItem('admin_refresh_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('admin_user') || 'null'))
  const profileLoaded = ref(false)

  const isAuthenticated = computed(() => !!token.value && user.value?.role === 'admin')

  function setTokens(accessToken, refreshTokenVal) {
    token.value = accessToken
    refreshToken.value = refreshTokenVal
    localStorage.setItem('admin_token', accessToken)
    localStorage.setItem('admin_refresh_token', refreshTokenVal)
  }

  function setUser(userData) {
    user.value = userData
    profileLoaded.value = true
    localStorage.setItem('admin_user', JSON.stringify(userData))
  }

  function setAuth(accessToken, refreshTokenVal, userData) {
    setTokens(accessToken, refreshTokenVal)
    setUser(userData)
  }

  function clearAuth() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    profileLoaded.value = false
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_refresh_token')
    localStorage.removeItem('admin_user')
  }

  async function fetchCurrentUser() {
    const res = await authApi.me()
    if (res.data.role !== 'admin') {
      clearAuth()
      throw new Error('该账号无管理员权限')
    }
    setUser(res.data)
    return res.data
  }

  async function ensureCurrentUser(force = false) {
    if (!token.value) {
      clearAuth()
      return null
    }
    if (!force && profileLoaded.value && user.value?.role === 'admin') {
      return user.value
    }
    return fetchCurrentUser()
  }

  async function login(account, password) {
    const res = await authApi.login(account, password, 'admin')
    if (res.data.user.role !== 'admin') {
      throw new Error('该账号无管理员权限')
    }
    setAuth(res.data.access_token, res.data.refresh_token, res.data.user)
    await fetchCurrentUser()
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
      setTokens(res.data.access_token, res.data.refresh_token)
      await fetchCurrentUser()
    } catch {
      clearAuth()
      router.replace('/login')
      throw new Error('登录已过期，请重新登录')
    }
  }

  return {
    token,
    refreshToken,
    user,
    profileLoaded,
    isAuthenticated,
    setTokens,
    setUser,
    setAuth,
    clearAuth,
    fetchCurrentUser,
    ensureCurrentUser,
    login,
    logout,
    refreshAccessToken,
  }
})
