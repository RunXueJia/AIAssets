<template>
  <el-container class="admin-shell">
    <el-aside
      class="admin-aside"
      width="236px"
    >
      <div class="brand">
        <div class="brand-mark">
          24
        </div>
        <div>
          <strong>Hours24</strong>
          <span>内容资产系统</span>
        </div>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        class="side-menu"
      >
        <el-menu-item
          v-for="item in visibleRoutes"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.meta.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="admin-header">
        <div>
          <div class="crumb">
            {{ $route.meta.title }}
          </div>
          <div class="header-caption">
            MVP 链路：配置栏目 -> 生成内容 -> 审核 -> 资产 -> 发布
          </div>
        </div>
        <div class="header-actions">
          <el-tag
            type="success"
            effect="plain"
          >
            {{ auth.user?.roles?.join(', ') }}
          </el-tag>
          <span>{{ auth.user?.display_name }}</span>
          <el-button
            text
            @click="handleLogout"
          >
            退出
          </el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import {
  Collection,
  Cpu,
  DataAnalysis,
  DocumentChecked,
  Files,
  Setting,
  TrendCharts
} from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { menuRoutes } from '@/router'
import { useAuthStore } from '@/store/auth'

const iconMap = {
  dashboard: DataAnalysis,
  content: Collection,
  llm: Cpu,
  review: DocumentChecked,
  assets: Files,
  reports: TrendCharts,
  system: Setting
}

const router = useRouter()
const auth = useAuthStore()

const visibleRoutes = computed(() =>
  menuRoutes
    .filter((route) => auth.can(route.meta.permission))
    .map((route) => ({ ...route, icon: iconMap[route.name] }))
)

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped lang="scss">
.admin-shell {
  min-height: 100vh;
}

.admin-aside {
  background: #102326;
  color: #d9eeee;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 72px;
  padding: 0 18px;
  border-bottom: 1px solid rgb(255 255 255 / 8%);

  strong,
  span {
    display: block;
  }

  span {
    margin-top: 3px;
    color: #91abad;
    font-size: 12px;
  }
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #0f766e;
  color: #fff;
  font-weight: 800;
}

.side-menu {
  border: 0;
  background: transparent;

  :deep(.el-menu-item) {
    color: #b9d2d4;
  }

  :deep(.el-menu-item.is-active) {
    background: rgb(15 118 110 / 22%);
    color: #fff;
  }
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72px;
  background: var(--h24-panel);
  border-bottom: 1px solid var(--h24-line);
}

.crumb {
  font-size: 18px;
  font-weight: 700;
}

.header-caption {
  margin-top: 4px;
  color: var(--h24-muted);
  font-size: 13px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-main {
  padding: 20px;
}
</style>
