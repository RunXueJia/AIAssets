<template>
  <main class="login-page">
    <section class="login-panel surface">
      <div class="login-copy">
        <div class="brand-line">
          Hours24
        </div>
        <h1>AI 内容资产生产后台</h1>
        <p>管理内容方向、LLM 生成、审核、视频资产、发布队列和增长数据。</p>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleLogin"
      >
        <el-form-item
          label="账号"
          prop="username"
        >
          <el-input
            v-model="form.username"
            size="large"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item
          label="密码"
          prop="password"
        >
          <el-input
            v-model="form.password"
            size="large"
            type="password"
            autocomplete="current-password"
          />
        </el-form-item>
        <div class="captcha-slot">
          验证码预留位
        </div>
        <el-button
          class="login-button"
          type="primary"
          size="large"
          :loading="loading"
          @click="handleLogin"
        >
          登录后台
        </el-button>
      </el-form>
    </section>
  </main>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'password' })
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.login(form)
    router.push(route.query.redirect || '/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  display: grid;
  place-items: center;
  min-height: 100vh;
  background:
    linear-gradient(115deg, rgb(15 118 110 / 13%), transparent 48%),
    #edf4f4;
}

.login-panel {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  width: 860px;
  padding: 32px;
}

.login-copy {
  padding-right: 42px;
  border-right: 1px solid var(--h24-line);

  h1 {
    max-width: 420px;
    margin: 22px 0 14px;
    font-size: 42px;
    line-height: 1.12;
    text-wrap: pretty;
  }

  p {
    max-width: 420px;
    color: var(--h24-muted);
    font-size: 16px;
    line-height: 1.8;
  }
}

.brand-line {
  color: var(--h24-primary);
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0;
}

.el-form {
  padding-left: 42px;
}

.captcha-slot {
  display: grid;
  place-items: center;
  height: 44px;
  margin-bottom: 18px;
  border: 1px dashed var(--h24-line);
  border-radius: 8px;
  color: var(--h24-muted);
  font-size: 13px;
}

.login-button {
  width: 100%;
}
</style>
