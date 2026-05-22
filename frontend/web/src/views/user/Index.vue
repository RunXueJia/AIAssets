<template>
  <div class="user-page">
    <template v-if="auth.isLoggedIn">
      <div class="profile-card">
        <div class="avatar-lg">{{ (auth.user?.nickname || '用')[0] }}</div>
        <div class="profile-info">
          <span class="nickname">{{ auth.user?.nickname || '用户' }}</span>
          <span class="role-badge">{{ auth.user?.role === 'admin' ? '管理员' : '用户' }}</span>
        </div>
      </div>

      <div class="menu-list">
        <div class="menu-item" @click="$router.push('/history')">
          <span class="menu-label">
            <el-icon><Tickets /></el-icon>
            历史记录
          </span>
          <el-icon><ArrowRight /></el-icon>
        </div>
        <div class="menu-item" @click="auth.logout()">
          <span class="menu-label">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </span>
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </template>

    <div v-else class="guest-block">
      <div class="guest-icon">
        <el-icon><User /></el-icon>
      </div>
      <p class="guest-text">登录后可跨设备同步规划记录</p>
      <el-button type="primary" size="large" class="guest-btn" @click="$router.push('/login')">
        去登录
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ArrowRight, SwitchButton, Tickets, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<style lang="scss" scoped>
.user-page {
  max-width: 480px;
  margin: 0 auto;
  padding-top: 16px;
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: $content-bg;
  border-radius: $radius-lg;
  box-shadow: $shadow-card;
  margin-bottom: 16px;
}

.avatar-lg {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, $color-primary, $color-primary-light);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nickname {
  font-size: 18px;
  font-weight: 600;
}

.role-badge {
  font-size: $font-size-xs;
  padding: 2px 10px;
  border-radius: 10px;
  background: $page-bg;
  color: $text-secondary;
  display: inline-block;
  width: fit-content;
}

.menu-list {
  background: $content-bg;
  border-radius: $radius-lg;
  box-shadow: $shadow-card;
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  font-size: $font-size-body;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 0.5px solid $border-card;

  &:last-child { border-bottom: none; }

  &:hover { background: $page-bg; }

  span { font-weight: 500; }
}

.guest-block {
  text-align: center;
  padding: 64px 24px;
}

.menu-label {
  display: inline-flex;
  align-items: center;
  gap: 10px;

  .el-icon {
    color: $color-primary;
    font-size: 18px;
  }
}

.guest-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 62px;
  height: 62px;
  margin-bottom: 16px;
  color: #fff;
  background: $color-ink;
  border-radius: 22px;
  box-shadow: $shadow-md;

  :deep(svg) {
    width: 30px;
    height: 30px;
  }
}

.guest-text {
  color: $text-secondary;
  margin-bottom: 24px;
  font-size: $font-size-body;
}

.guest-btn {
  height: 46px;
  padding: 0 40px;
  font-weight: 600;
}
</style>
