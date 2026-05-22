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
  background: transparent;
}

.mobile-content {
  min-height: 100vh;
  min-height: 100dvh;
  padding: 12px 12px calc($tab-height + env(safe-area-inset-bottom, 0px) + 18px);
}

.bottom-tabs {
  position: fixed;
  bottom: 10px;
  left: 12px;
  right: 12px;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: space-around;
  height: $tab-height;
  background: rgba($content-bg, 0.91);
  backdrop-filter: blur(22px) saturate(1.08);
  -webkit-backdrop-filter: blur(22px) saturate(1.08);
  border: 1px solid rgba($border-light, 0.86);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba($text-primary, 0.13);
  padding: 6px 8px calc(6px + env(safe-area-inset-bottom, 0));
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  color: $text-secondary;
  text-decoration: none;
  padding: 8px 14px;
  position: relative;
  min-width: 68px;
  min-height: 50px;
  justify-content: center;
  border-radius: 18px;
  transition:
    color 0.18s ease,
    background 0.18s ease,
    transform 0.18s ease;

  &.active {
    color: $color-primary;
    font-weight: 600;
    background: $color-primary-bg;

    .tab-icon {
      transform: translateY(-1px);
    }
  }

  &:active {
    transform: scale(0.97);
  }
}

.tab-icon {
  width: 22px;
  height: 22px;
  display: block;
  transition: transform 0.18s ease;
}

.tab-label {
  font-size: 11px;
  font-weight: 650;
  line-height: 1;
}
</style>
