<template>
  <div class="login-page">
    <div class="login-card">
      <h2>路书匠 · 管理后台</h2>
      <el-form ref="formRef" :model="form" @submit.prevent="handleLogin">
        <el-form-item prop="account" :rules="[{ required: true, message: '请输入账号' }]">
          <el-input v-model="form.account" placeholder="管理员账号" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password" :rules="[{ required: true, message: '请输入密码' }]">
          <el-input v-model="form.password" type="password" show-password placeholder="密码" prefix-icon="Lock" size="large" />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading" class="login-btn" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
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
    const redirect = route.query.redirect || '/dashboard'
    router.replace(redirect)
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
  min-height: 100vh;
  background: $page-bg;
}

.login-card {
  width: 400px;
  padding: 48px 40px;
  background: $content-bg;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);

  h2 {
    text-align: center;
    margin-bottom: 36px;
    font-size: 20px;
    color: $text-primary;
  }
}

.login-btn {
  width: 100%;
  margin-top: 12px;
}
</style>
