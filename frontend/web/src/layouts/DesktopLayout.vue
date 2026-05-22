<template>
  <div class="desktop-layout">
    <header class="top-nav">
      <div class="nav-inner">
        <router-link to="/" class="brand">
          <span class="brand-icon">
            <el-icon><Compass /></el-icon>
          </span>
          <span class="brand-copy">
            <span class="brand-text">路书匠</span>
            <span class="brand-sub">生活规划助手</span>
          </span>
        </router-link>
        <nav class="nav-links">
          <router-link to="/" class="nav-pill">
            <el-icon><EditPen /></el-icon>
            <span>规划</span>
          </router-link>
          <router-link to="/history" class="nav-pill">
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
import { Clock, Compass, EditPen } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<style lang="scss" scoped>
.desktop-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0)),
    transparent;
}

.top-nav {
  height: $nav-height;
  background: rgba($surface-soft, 0.84);
  backdrop-filter: blur(22px) saturate(1.08);
  -webkit-backdrop-filter: blur(22px) saturate(1.08);
  border-bottom: 1px solid rgba($border-light, 0.72);
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
  padding: 0 32px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  color: $text-primary;
  min-height: 44px;
}

.brand-icon {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.18), transparent),
    $color-primary;
  box-shadow: 0 12px 24px rgba($color-primary, 0.22);

  :deep(svg) {
    width: 21px;
    height: 21px;
  }
}

.brand-copy {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.brand-text {
  font-weight: 750;
  font-size: 18px;
  letter-spacing: 0;
}

.brand-sub {
  margin-top: 3px;
  font-size: 11px;
  font-weight: 550;
  color: $text-hint;
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
    min-height: 38px;
    padding: 8px 15px;
    border-radius: 999px;
    font-weight: 650;
    transition:
      color 0.18s ease,
      background 0.18s ease,
      box-shadow 0.18s ease,
      transform 0.18s ease;

    &:hover {
      color: $text-primary;
      background: rgba($content-bg, 0.72);
      box-shadow: $shadow-sm;
      transform: translateY(-1px);
    }

    &.router-link-active {
      color: $text-primary;
      background: $content-bg;
      box-shadow: $shadow-sm;
    }
  }
}

.login-link {
  background: $color-primary !important;
  color: #fff !important;
  padding: 8px 20px !important;
  font-weight: 700;
  box-shadow: 0 10px 22px rgba($color-primary, 0.22);

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
  min-height: 38px;
  padding: 4px 12px 4px 5px;
  border-radius: 999px;
  font-size: $font-size-sm;
  font-weight: 650;
  transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;

  &:hover {
    color: $text-primary;
    background: $content-bg;
    box-shadow: $shadow-sm;
  }
}

.avatar-sm {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: $color-ink;
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
  padding: 26px 32px 44px;
}
</style>
