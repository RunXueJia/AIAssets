import { useAuthStore } from '@/stores/auth'

export function setupGuards(router) {
  router.beforeEach(async (to, from, next) => {
    const auth = useAuthStore()

    if (to.meta?.title) {
      document.title = `${to.meta.title} · 路书匠管理后台`
    }

    if (to.meta.requiresAuth) {
      try {
        await auth.ensureCurrentUser()
      } catch {
        next({ path: '/login', query: { redirect: to.fullPath } })
        return
      }

      if (!auth.isAuthenticated) {
        next({ path: '/login', query: { redirect: to.fullPath } })
        return
      }
    }

    if (to.meta.requiresAdmin && auth.user?.role !== 'admin') {
      next({ path: '/login' })
      return
    }

    if (to.path === '/login' && auth.isAuthenticated) {
      next('/dashboard')
    } else {
      next()
    }
  })
}
