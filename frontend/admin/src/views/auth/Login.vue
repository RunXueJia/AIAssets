<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="login-brand">
        <div class="brand-badge">路</div>
        <div>
          <p class="brand-kicker">RouteCraft Admin</p>
          <h1>路书匠运营控制台</h1>
          <p class="brand-copy">统一管理用户、生成记录与 LLM 配置。</p>
        </div>
      </section>

      <section class="login-card">
        <div class="login-card-header">
          <p class="login-kicker">管理员登录</p>
          <h2>进入后台</h2>
        </div>
        <el-form ref="formRef" :model="form" @submit.prevent="handleLogin">
          <el-form-item prop="account" :rules="[{ required: true, message: '请输入账号' }]">
            <el-input v-model="form.account" placeholder="管理员账号" prefix-icon="User" size="large" />
          </el-form-item>
          <el-form-item prop="password" :rules="[{ required: true, message: '请输入密码' }]">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="密码"
              prefix-icon="Lock"
              size="large"
            />
          </el-form-item>
          <el-button type="primary" size="large" :loading="loading" class="login-btn" @click="handleLogin">
            登录
          </el-button>
        </el-form>
      </section>
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
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  min-height: 100vh;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(17, 24, 39, 0.92), rgba(15, 23, 42, 0.78)),
    radial-gradient(circle at 20% 20%, rgba(37, 99, 235, 0.4), transparent 32rem),
    $sidebar-bg;

  &::before {
    position: absolute;
    inset: 10% auto auto 8%;
    width: 360px;
    height: 360px;
    content: "";
    background: rgba(14, 165, 233, 0.18);
    border-radius: 999px;
    filter: blur(60px);
  }
}

.login-shell {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(280px, 1fr) 420px;
  gap: 28px;
  width: min(960px, 100%);
  align-items: stretch;
}

.login-brand {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 460px;
  padding: 42px;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: $radius-lg;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04)),
    rgba(255, 255, 255, 0.06);
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.18);
  backdrop-filter: blur(16px);
}

.brand-badge {
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  color: #fff;
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, $color-primary, #0f766e);
  border-radius: $radius-lg;
  box-shadow: 0 18px 40px rgba(37, 99, 235, 0.28);
}

.brand-kicker {
  margin-top: auto;
  color: rgba(226, 232, 240, 0.72);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-brand h1 {
  max-width: 420px;
  margin-top: 12px;
  font-size: 38px;
  font-weight: 800;
  line-height: 1.12;
  letter-spacing: 0;
}

.brand-copy {
  max-width: 360px;
  margin-top: 16px;
  color: rgba(241, 245, 249, 0.78);
  font-size: 15px;
  line-height: 1.7;
  text-wrap: pretty;
}

.login-card {
  align-self: center;
  width: 100%;
  padding: 38px 36px;
  background: $content-bg;
  border: 1px solid rgba(255, 255, 255, 0.74);
  border-radius: $radius-lg;
  box-shadow: $shadow-float;

  h2 {
    margin-bottom: 26px;
    font-size: 26px;
    font-weight: 800;
    color: $text-primary;
  }
}

.login-card-header {
  margin-bottom: 24px;
}

.login-kicker {
  margin-bottom: 6px;
  color: $text-muted;
  font-size: 13px;
  font-weight: 700;
}

.login-btn {
  width: 100%;
  margin-top: 12px;
  min-height: 42px;
}

@media (max-width: 820px) {
  .login-page {
    padding: 20px;
  }

  .login-shell {
    grid-template-columns: 1fr;
  }

  .login-brand {
    min-height: auto;
    padding: 28px;
  }

  .login-brand h1 {
    font-size: 30px;
  }

  .login-card {
    padding: 30px 24px;
  }
}
</style>
