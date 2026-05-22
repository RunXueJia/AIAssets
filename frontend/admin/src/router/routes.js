export const staticRoutes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '管理员登录' },
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '首页' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/Index.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'users/:userId',
        name: 'UserDetail',
        component: () => import('@/views/users/Detail.vue'),
        meta: { title: '用户详情' },
      },
      {
        path: 'records',
        name: 'Records',
        component: () => import('@/views/records/Index.vue'),
        meta: { title: '生成记录' },
      },
      {
        path: 'records/:recordId',
        name: 'RecordDetail',
        component: () => import('@/views/records/Detail.vue'),
        meta: { title: '记录详情' },
      },
      {
        path: 'llm-config',
        name: 'LlmConfig',
        component: () => import('@/views/llm-config/Index.vue'),
        meta: { title: 'LLM 配置' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '404' },
  },
]
