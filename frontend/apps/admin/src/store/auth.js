import { defineStore } from 'pinia'
import { authApi } from '@/api'
import { setToken } from '@/utils/apiClient'
import { hasPermission } from '@/utils/permissions'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    bootstrapped: false
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.user),
    permissions: (state) => state.user?.permissions || [],
    can: (state) => (required) => hasPermission(state.user?.permissions || [], required)
  },
  actions: {
    async login(form) {
      const data = await authApi.login(form)
      setToken(data.access_token)
      this.user = data.user
      this.bootstrapped = true
      return data
    },
    async bootstrap() {
      if (this.bootstrapped) {
        return
      }
      try {
        this.user = await authApi.getCurrentUser()
      } catch {
        this.user = null
      } finally {
        this.bootstrapped = true
      }
    },
    async logout() {
      try {
        await authApi.logout()
      } finally {
        this.clearSession()
      }
    },
    clearSession() {
      setToken('')
      this.user = null
      this.bootstrapped = true
    }
  }
})
