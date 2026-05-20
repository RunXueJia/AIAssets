import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { auth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '首页概览', icon: 'HomeFilled', auth: true },
      },
      {
        path: 'generation/create',
        name: 'GenerationCreate',
        component: () => import('@/views/generation/CreateView.vue'),
        meta: { title: '内容生成', icon: 'Edit', auth: true, roles: ['admin', 'operation_manager'] },
      },
      {
        path: 'generation/process/:id',
        name: 'GenerationProcess',
        component: () => import('@/views/generation/ProcessView.vue'),
        meta: { title: '生成过程', auth: true, hidden: true },
      },
      {
        path: 'generation/tasks',
        name: 'GenerationTasks',
        component: () => import('@/views/generation/TaskListView.vue'),
        meta: { title: '生成任务', icon: 'List', auth: true },
      },
      {
        path: 'source/list',
        name: 'SourceList',
        component: () => import('@/views/source/SourceListView.vue'),
        meta: { title: '素材来源', icon: 'Link', auth: true },
      },
      {
        path: 'source/summary/:id',
        name: 'SourceSummary',
        component: () => import('@/views/source/SummaryView.vue'),
        meta: { title: '素材汇总详情', auth: true, hidden: true },
      },
      {
        path: 'topic/list',
        name: 'TopicList',
        component: () => import('@/views/topic/TopicListView.vue'),
        meta: { title: '选题管理', icon: 'Collection', auth: true },
      },
      {
        path: 'topic/detail/:id',
        name: 'TopicDetail',
        component: () => import('@/views/topic/TopicDetailView.vue'),
        meta: { title: '选题详情', auth: true, hidden: true },
      },
      {
        path: 'script/detail/:id',
        name: 'ScriptDetail',
        component: () => import('@/views/script/ScriptDetailView.vue'),
        meta: { title: '脚本与分镜', auth: true, hidden: true },
      },
      {
        path: 'review/list',
        name: 'ReviewList',
        component: () => import('@/views/review/ReviewListView.vue'),
        meta: { title: '内容审核', icon: 'Checked', auth: true, roles: ['admin', 'operation_manager', 'content_editor'] },
      },
      {
        path: 'monitor/list',
        name: 'MonitorList',
        component: () => import('@/views/monitor/MonitorListView.vue'),
        meta: { title: '话题监控', icon: 'Monitor', auth: true, roles: ['admin', 'operation_manager'] },
      },
      {
        path: 'monitor/summary',
        name: 'DailySummary',
        component: () => import('@/views/monitor/DailySummaryView.vue'),
        meta: { title: '每日汇总', auth: true, hidden: true },
      },
      {
        path: 'render/list',
        name: 'RenderList',
        component: () => import('@/views/render/RenderListView.vue'),
        meta: { title: '视频合成', icon: 'VideoCamera', auth: true, roles: ['admin', 'video_operator'] },
      },
      {
        path: 'package/list',
        name: 'PackageList',
        component: () => import('@/views/package/PackageListView.vue'),
        meta: { title: '发布包管理', icon: 'FolderOpened', auth: true },
      },
      {
        path: 'package/detail/:id',
        name: 'PackageDetail',
        component: () => import('@/views/package/PackageDetailView.vue'),
        meta: { title: '发布包详情', auth: true, hidden: true },
      },
      {
        path: 'publish/records',
        name: 'PublishRecords',
        component: () => import('@/views/publish/PublishRecordView.vue'),
        meta: { title: '发布记录', icon: 'Promotion', auth: true, roles: ['admin', 'video_operator'] },
      },
      {
        path: 'report/list',
        name: 'ReportList',
        component: () => import('@/views/report/ReportListView.vue'),
        meta: { title: '每日报告', icon: 'DocumentChecked', auth: true },
      },
      {
        path: 'report/detail/:id',
        name: 'ReportDetail',
        component: () => import('@/views/report/ReportDetailView.vue'),
        meta: { title: '报告详情', auth: true, hidden: true },
      },
      {
        path: 'setting',
        name: 'Setting',
        component: () => import('@/views/setting/SettingView.vue'),
        meta: { title: '系统设置', icon: 'Setting', auth: true, roles: ['admin'] },
      },
    ],
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/ForbiddenView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  if (to.meta.auth === false) {
    if (auth.isLoggedIn && to.name === 'Login') {
      return next('/dashboard')
    }
    return next()
  }

  if (!auth.isLoggedIn) {
    return next('/login')
  }

  if (!auth.user) {
    await auth.fetchUser()
  }

  if (to.meta.roles && to.meta.roles.length > 0) {
    const allowed = to.meta.roles.some((r) => auth.role === r || r === '*')
    if (!allowed) {
      return next('/403')
    }
  }

  next()
})

export default router
