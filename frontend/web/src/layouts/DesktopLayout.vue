<template>
  <div class="desktop-layout">
    <header class="top-nav">
      <div class="nav-inner">
        <router-link to="/" class="brand">
          <span class="brand-icon">🗺</span>
          <span class="brand-text">路书匠</span>
        </router-link>
        <nav class="nav-links">
          <router-link to="/history">
            <el-icon><Clock /></el-icon>
            <span>历史</span>
          </router-link>
          <template v-if="auth.isLoggedIn">
            <el-dropdown trigger="click">
              <span class="user-trigger">
                <span class="avatar-sm">{{ (auth.user?.nickname || '用')[0] }}</span>
                <span>{{ auth.user?.nickname }}</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="auth.logout()">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <router-link v-else to="/login" class="login-link">登录</router-link>
        </nav>
      </div>
    </header>
    <main class="desktop-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { Clock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<style lang="scss" scoped>
.desktop-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.top-nav {
  height: $nav-height;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-inner {
  max-width: $max-content-width;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  color: $text-primary;
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 0.5px;
}

.brand-icon {
  font-size: 22px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: $font-size-sm;

  a {
    display: flex;
    align-items: center;
    gap: 5px;
    color: $text-secondary;
    padding: 6px 14px;
    border-radius: 20px;
    transition: all 0.15s;

    &:hover {
      color: $text-primary;
      background: rgba(0, 0, 0, 0.04);
    }
  }
}

.login-link {
  background: $color-primary !important;
  color: #fff !important;
  padding: 6px 18px !important;
  font-weight: 500;

  &:hover {
    background: $color-primary-light !important;
    color: #fff !important;
  }
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: $text-secondary;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: $font-size-sm;
  transition: background 0.15s;

  &:hover {
    background: rgba(0, 0, 0, 0.04);
  }
}

.avatar-sm {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, $color-primary, $color-primary-light);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}

.desktop-main {
  flex: 1;
  max-width: $max-content-width;
  width: 100%;
  margin: 0 auto;
  padding: 20px 28px;
}
</style>
