import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import App from './App.vue'
import './styles/global.scss'

const routes = [
  { path: '/', component: () => import('@/pages/Home.vue') },
  { path: '/columns', component: () => import('@/pages/Columns.vue') },
  { path: '/articles/:slug', component: () => import('@/pages/ArticleDetail.vue') },
  { path: '/videos/:id', component: () => import('@/pages/VideoDetail.vue') },
  { path: '/downloads', component: () => import('@/pages/Downloads.vue') },
  { path: '/tools', component: () => import('@/pages/Tools.vue') }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

createApp(App).use(router).mount('#app')
