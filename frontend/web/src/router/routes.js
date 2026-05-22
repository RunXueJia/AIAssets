export const staticRoutes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/planning/Index.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/result/:recordId',
    name: 'Result',
    component: () => import('@/views/planning/Result.vue'),
    meta: { title: '规划结果' },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/history/Index.vue'),
    meta: { title: '历史记录' },
  },
  {
    path: '/history/:recordId',
    name: 'HistoryDetail',
    component: () => import('@/views/history/Detail.vue'),
    meta: { title: '记录详情' },
  },
  {
    path: '/user',
    name: 'User',
    component: () => import('@/views/user/Index.vue'),
    meta: { title: '我的' },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/user/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '404' },
  },
]
