<template>
  <div class="mobile-layout">
    <main class="mobile-content">
      <router-view />
    </main>
    <nav class="bottom-tabs">
      <router-link
        v-for="tab in tabs"
        :key="tab.path"
        :to="tab.path"
        class="tab-item"
        :class="{ active: isTabActive(tab.path) }"
      >
        <component :is="tab.icon" class="tab-icon" />
        <span class="tab-label">{{ tab.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { EditPen, Clock, User } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { path: '/', label: '首页', icon: EditPen },
  { path: '/history', label: '历史', icon: Clock },
  { path: '/user', label: '我的', icon: User },
]

function isTabActive(tabPath) {
  if (tabPath === '/') {
    return route.path === '/' || route.path.startsWith('/result')
  }
  return route.path.startsWith(tabPath)
}
</script>

<style lang="scss" scoped>
.mobile-layout {
  min-height: 100vh;
  min-height: 100dvh;
}

.mobile-content {
  padding-bottom: calc($tab-height + env(safe-area-inset-bottom, 0px) + 8px);
}

.bottom-tabs {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: space-around;
  height: $tab-height;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 0.5px solid rgba(0, 0, 0, 0.08);
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  color: $text-secondary;
  text-decoration: none;
  padding: 8px 16px 4px;
  position: relative;
  min-width: 56px;
  min-height: 44px;
  justify-content: center;
  transition: color 0.2s;

  &.active {
    color: $color-primary;
    font-weight: 600;
  }
}

.tab-icon {
  width: 22px;
  height: 22px;
  display: block;
}

.tab-label {
  font-size: 10px;
  line-height: 1;
}
</style>
