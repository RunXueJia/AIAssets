<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="logo">路书匠 · 管理后台</div>
      <el-menu
        :default-active="activeMenu"
        background-color="#1d1e2c"
        text-color="#bfcbd9"
        active-text-color="#409eff"
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
        <span class="header-user">{{ auth.user?.nickname || '管理员' }}</span>
        <el-button text @click="auth.logout()">退出</el-button>
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
</script>
