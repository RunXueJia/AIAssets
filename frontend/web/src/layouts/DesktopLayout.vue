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
  background: $page-bg;
}

.top-nav {
  height: $nav-height;
  background:
    radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.3), transparent 48%),
    linear-gradient(180deg, rgba(255, 255, 252, 0.72), rgba(248, 246, 237, 0.54));
  backdrop-filter: blur(20px) saturate(1.08);
  -webkit-backdrop-filter: blur(20px) saturate(1.08);
  border-bottom: 1px solid rgba(255, 255, 255, 0.44);
  box-shadow: 0 18px 34px rgba(0, 0, 0, 0.26);
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
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: $color-ink;
  background:
    radial-gradient(circle at 46% 24%, rgba(255, 255, 255, 1), rgba(255, 255, 255, 0.58) 48%, transparent 70%),
    linear-gradient(145deg, rgba(255, 255, 252, 0.98), rgba(226, 222, 207, 0.88));
  box-shadow:
    0 1px 1px rgba(255, 255, 255, 0.98) inset,
    0 -9px 18px rgba(186, 178, 153, 0.14) inset,
    0 11px 21px rgba(0, 0, 0, 0.24);

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
    border-radius: 8px;
    font-weight: 650;
    transition:
      color 0.18s ease,
      background 0.18s ease,
      box-shadow 0.18s ease,
      transform 0.18s ease;

    &:hover {
      color: $color-ink;
      background:
        radial-gradient(circle at 50% 18%, rgba(255, 255, 255, 0.92), transparent 58%),
        linear-gradient(145deg, rgba(255, 255, 252, 0.96), rgba(229, 225, 212, 0.84));
      box-shadow:
        0 1px 1px rgba(255, 255, 255, 0.98) inset,
        0 10px 18px rgba(0, 0, 0, 0.2);
      transform: translateY(-1px);
    }

    &.router-link-active {
      color: $color-ink;
      background:
        radial-gradient(circle at 50% 18%, rgba(255, 255, 255, 1), transparent 56%),
        linear-gradient(145deg, rgba(255, 255, 252, 0.98), rgba(226, 222, 207, 0.9));
      box-shadow:
        0 1px 1px rgba(255, 255, 255, 1) inset,
        0 -8px 16px rgba(186, 178, 153, 0.14) inset,
        0 10px 20px rgba(0, 0, 0, 0.22);
    }
  }
}

.login-link {
  background:
    radial-gradient(circle at 50% 18%, rgba(255, 255, 255, 1), transparent 56%),
    linear-gradient(145deg, rgba(255, 255, 252, 0.98), rgba(226, 222, 207, 0.9)) !important;
  color: $color-ink !important;
  padding: 8px 20px !important;
  font-weight: 700;
  box-shadow:
    0 1px 1px rgba(255, 255, 255, 1) inset,
    0 -8px 16px rgba(186, 178, 153, 0.14) inset,
    0 10px 20px rgba(0, 0, 0, 0.22);

  &:hover {
    background:
      radial-gradient(circle at 50% 18%, rgba(255, 255, 255, 1), transparent 56%),
      linear-gradient(145deg, rgba(255, 255, 255, 1), rgba(237, 233, 218, 0.92)) !important;
    color: $color-ink !important;
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
  border-radius: 8px;
  font-size: $font-size-sm;
  font-weight: 650;
  transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;

  &:hover {
    color: $text-primary;
    background: rgba(255, 255, 255, 0.08);
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.08) inset;
  }
}

.avatar-sm {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 50% 24%, rgba(255, 255, 255, 1), transparent 60%),
    linear-gradient(145deg, rgba(255, 255, 252, 0.98), rgba(224, 219, 204, 0.9));
  color: $color-ink;
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

// Neumorphic soft UI override
.top-nav {
  background: $content-bg;
  border-bottom: 0;
  box-shadow:
    -6px -6px 14px rgba(255, 255, 255, 0.54),
    6px 6px 14px rgba(163, 177, 198, 0.22);
}

.brand-icon,
.nav-links a.router-link-active,
.login-link,
.avatar-sm {
  background: $content-bg !important;
  color: $text-primary !important;
  box-shadow: $shadow-sm;
}

.nav-links a,
.user-trigger {
  border-radius: 14px;
}

.nav-links a:hover,
.user-trigger:hover {
  background: $content-bg;
  color: $text-primary;
  box-shadow: $shadow-sm;
}

.nav-links a:active,
.login-link:active,
.user-trigger:active {
  transform: translateY(1px) scale(0.99);
  box-shadow:
    inset -5px -5px 10px rgba(255, 255, 255, 0.68),
    inset 5px 5px 10px rgba(163, 177, 198, 0.42);
}
</style>
