<template>
  <el-container class="main-layout">
    <el-aside :width="app.sidebarCollapsed ? '64px' : '220px'" class="main-aside">
      <div class="logo-area" @click="app.toggleSidebar">
        <span v-if="!app.sidebarCollapsed" class="logo-text">24h AI 引擎</span>
        <span v-else class="logo-text-short">24</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="app.sidebarCollapsed"
        :collapse-transition="false"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <template v-for="route in visibleRoutes" :key="route.path">
          <el-sub-menu v-if="route.children && route.children.length" :index="'/' + route.path">
            <template #title>
              <el-icon v-if="route.meta?.icon"><component :is="route.meta.icon" /></el-icon>
              <span>{{ route.meta?.title || route.name }}</span>
            </template>
            <el-menu-item v-for="child in route.children" :key="child.path" :index="'/' + child.path">
              {{ child.meta?.title || child.name }}
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="'/' + route.path">
            <el-icon v-if="route.meta?.icon"><component :is="route.meta.icon" /></el-icon>
            <template #title>{{ route.meta?.title || route.name }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="main-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="app.toggleSidebar">
            <Fold v-if="!app.sidebarCollapsed" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-info">
              {{ auth.user?.display_name || auth.user?.username }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const app = useAppStore()

const activeMenu = computed(() => route.path)

const visibleRoutes = computed(() => {
  return router.options.routes
    .find((r) => r.path === '/')
    ?.children?.filter((r) => {
      if (r.meta?.hidden) return false
      if (r.meta?.roles && r.meta.roles.length > 0) {
        return r.meta.roles.some((role) => auth.role === role || role === '*')
      }
      return true
    }) || []
})

const breadcrumbs = computed(() => {
  const items = [{ title: '首页', path: '/dashboard' }]
  if (route.meta?.title && route.path !== '/dashboard') {
    items.push({ title: route.meta.title, path: route.path })
  }
  return items
})

function handleCommand(cmd) {
  if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
}

.main-aside {
  background: #304156;
  overflow: hidden;
  transition: width 0.3s;
}

.logo-area {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-text-short {
  font-size: 24px;
}

.el-menu {
  border-right: none;
}

.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-btn {
  font-size: 18px;
  cursor: pointer;
  color: #606266;
  &:hover { color: #409eff; }
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #303133;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
