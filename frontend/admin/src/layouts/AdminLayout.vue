<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="brand">
        <div class="brand-mark">路</div>
        <div class="brand-copy">
          <div class="brand-title">路书匠</div>
          <div class="brand-subtitle">运营控制台</div>
        </div>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/records">
          <el-icon><Document /></el-icon>
          <span>生成记录</span>
        </el-menu-item>
        <el-menu-item index="/llm-config">
          <el-icon><Setting /></el-icon>
          <span>LLM 配置</span>
        </el-menu-item>
      </el-menu>
    </aside>
    <div class="admin-main">
      <header class="admin-header">
        <div class="header-title">
          <span class="header-kicker">Admin Console</span>
          <span class="header-current">{{ currentTitle }}</span>
        </div>
        <div class="header-actions">
          <span class="header-user">{{ auth.user?.nickname || '管理员' }}</span>
          <el-button text @click="auth.logout()">退出</el-button>
        </div>
      </header>
      <div class="admin-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/users')) return '/users'
  if (path.startsWith('/records')) return '/records'
  if (path.startsWith('/llm-config')) return '/llm-config'
  return '/dashboard'
})

const currentTitle = computed(() => {
  const path = route.path
  if (path.startsWith('/users/')) return '用户详情'
  if (path.startsWith('/users')) return '用户管理'
  if (path.startsWith('/records/')) return '记录详情'
  if (path.startsWith('/records')) return '生成记录'
  if (path.startsWith('/llm-config')) return 'LLM 配置'
  return '控制台概览'
})
</script>
