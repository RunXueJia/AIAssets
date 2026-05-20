import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, logout as logoutApi, getMe } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  const permissions = ref([])

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => user.value?.role || '')

  function setToken(val) {
    token.value = val
    if (val) {
      localStorage.setItem('token', val)
    } else {
      localStorage.removeItem('token')
    }
  }

  async function login(username, password) {
    const res = await loginApi(username, password)
    setToken(res.access_token)
    user.value = res.user
    permissions.value = res.user?.permissions || []
    return res
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await getMe()
      user.value = res
      permissions.value = res.permissions || []
    } catch {
      logout()
    }
  }

  function logout() {
    setToken('')
    user.value = null
    permissions.value = []
    try { logoutApi() } catch {}
  }

  function hasPermission(perm) {
    if (permissions.value.length === 0) return false
    if (permissions.value.includes('*')) return true
    return permissions.value.includes(perm)
  }

  function hasAnyPermission(perms) {
    return perms.some((p) => hasPermission(p))
  }

  return { token, user, permissions, isLoggedIn, role, login, fetchUser, logout, hasPermission, hasAnyPermission }
})
