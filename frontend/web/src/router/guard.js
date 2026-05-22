import { useAuthStore } from '@/stores/auth'

export function setupGuards(router) {
  router.beforeEach((to, from, next) => {
    const auth = useAuthStore()

    // Page title
    if (to.meta?.title) {
      document.title = `${to.meta.title} · 路书匠`
    }

    if (to.meta.requiresAuth && !auth.isAuthenticated) {
      next({ path: '/login', query: { redirect: to.fullPath } })
    } else if (to.path === '/login' && auth.isLoggedIn) {
      next('/')
    } else {
      next()
    }
  })
}
