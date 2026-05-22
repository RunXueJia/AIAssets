<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-icon">
          <el-icon><MapLocation /></el-icon>
        </div>
        <h2>欢迎回来</h2>
        <p>登录路书匠，同步你的出行规划</p>
      </div>
      <el-form ref="formRef" :model="form" @submit.prevent="handleLogin">
        <el-form-item prop="account" :rules="[{ required: true, message: '请输入账号' }]">
          <el-input
            v-model="form.account"
            placeholder="用户名或邮箱"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password" :rules="[{ required: true, message: '请输入密码' }]">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>
      <p class="switch-text">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, Lock, MapLocation } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const loading = ref(false)
const formRef = ref(null)

const form = reactive({ account: '', password: '' })

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.login(form.account, form.password)
    ElMessage.success('登录成功')
    router.replace(route.query.redirect || '/')
  } catch (err) {
    ElMessage.error(err.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
  padding: 24px;
}

.login-card {
  width: 380px;
  padding: 40px 32px;
  background: $content-bg;
  border-radius: $radius-xl;
  box-shadow: $shadow-lg;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 54px;
  height: 54px;
  margin-bottom: 8px;
  color: #fff;
  background: linear-gradient(135deg, $color-primary, $color-primary-light);
  border-radius: 18px;
  box-shadow: 0 14px 28px rgba($color-primary, 0.22);

  :deep(svg) {
    width: 28px;
    height: 28px;
  }
}

.login-header h2 {
  font-size: 22px;
  font-weight: 700;
}

.login-header p {
  font-size: $font-size-sm;
  color: $text-secondary;
  margin-top: 6px;
}

.login-btn {
  width: 100%;
  height: 46px;
  margin-top: 8px;
  font-size: 15px;
  font-weight: 600;
}

.switch-text {
  text-align: center;
  margin-top: 24px;
  font-size: $font-size-sm;
  color: $text-secondary;

  a { color: $color-primary; font-weight: 500; }
}
</style>
