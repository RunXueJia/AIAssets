import { createRouter, createWebHistory } from 'vue-router'
import AdminLayout from '@/layouts/AdminLayout.vue'
import { useAuthStore } from '@/store/auth'

export const menuRoutes = [
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/pages/Dashboard.vue'),
    meta: { title: '今日看板', permission: 'dashboard:overview:read' }
  },
  {
    path: '/content',
    name: 'content',
    component: () => import('@/pages/ContentWorkbench.vue'),
    meta: { title: '内容生产', permission: 'content:topic:read' }
  },
  {
    path: '/llm',
    name: 'llm',
    component: () => import('@/pages/LlmCenter.vue'),
    meta: { title: 'LLM 中心', permission: 'llm:prompt:read' }
  },
  {
    path: '/review',
    name: 'review',
    component: () => import('@/pages/ReviewWorkspace.vue'),
    meta: { title: '审核工作台', permission: 'review:content:read' }
  },
  {
    path: '/assets',
    name: 'assets',
    component: () => import('@/pages/AssetPublish.vue'),
    meta: { title: '资产与发布', permission: 'asset:video:read' }
  },
  {
    path: '/reports',
    name: 'reports',
    component: () => import('@/pages/Reports.vue'),
    meta: { title: '任务与日报', permission: 'report:daily:read' }
  },
  {
    path: '/system',
    name: 'system',
    component: () => import('@/pages/SystemSettings.vue'),
    meta: { title: '系统配置', permission: 'system:user:read' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', name: 'login', component: () => import('@/pages/Login.vue') },
    { path: '/403', name: 'forbidden', component: () => import('@/pages/Forbidden.vue') },
    {
      path: '/',
      component: AdminLayout,
      children: menuRoutes
    }
  ]
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.bootstrap()

  if (to.name === 'login') {
    return auth.isLoggedIn ? '/dashboard' : true
  }

  if (!auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (!auth.can(to.meta.permission)) {
    return { name: 'forbidden' }
  }

  return true
})

export default router
