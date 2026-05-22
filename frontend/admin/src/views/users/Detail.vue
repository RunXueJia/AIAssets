<template>
  <div class="user-detail page-shell" v-loading="loading">
    <div class="back-bar">
      <el-button text @click="$router.push('/users')">
        <el-icon><ArrowLeft /></el-icon> 返回用户列表
      </el-button>
    </div>

    <template v-if="detail">
      <div class="detail-hero panel">
        <div class="avatar-mark">{{ userInitial }}</div>
        <div class="detail-summary">
          <div class="detail-title-row">
            <h2>{{ detail.nickname || detail.username }}</h2>
            <el-tag :type="detail.status === 'active' ? 'success' : 'danger'" size="small">
              {{ detail.status === 'active' ? '正常' : '已禁用' }}
            </el-tag>
          </div>
          <p>{{ detail.email || '未填写邮箱' }}</p>
        </div>
      </div>

      <div class="detail-grid">
        <section class="detail-panel panel">
          <div class="section-heading">
            <h3>账号信息</h3>
          </div>
          <el-descriptions :column="2" border class="detail-table">
            <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
            <el-descriptions-item label="用户名">{{ detail.username }}</el-descriptions-item>
            <el-descriptions-item label="昵称">{{ detail.nickname || '-' }}</el-descriptions-item>
            <el-descriptions-item label="角色">
              <el-tag size="small">{{ roleLabel(detail.role) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="生成次数">{{ detail.generation_count }}</el-descriptions-item>
            <el-descriptions-item label="最后登录">{{ detail.last_login_at || '-' }}</el-descriptions-item>
            <el-descriptions-item label="注册时间" :span="2">{{ detail.created_at }}</el-descriptions-item>
          </el-descriptions>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { adminApi } from '@/api/admin'
import { useLoading } from '@/composables/useLoading'

const route = useRoute()
const { loading, withLoading } = useLoading()
const detail = ref(null)
const userInitial = computed(() => (detail.value?.nickname || detail.value?.username || '用').slice(0, 1).toUpperCase())

function roleLabel(r) {
  const map = { admin: '管理员', user: '用户', guest: '游客' }
  return map[r] || r
}

const fetchDetail = withLoading(async () => {
  const res = await adminApi.getUserDetail(route.params.userId)
  detail.value = res.data
})

onMounted(() => fetchDetail())
</script>

<style lang="scss" scoped>
.user-detail {
  max-width: 1040px;
}

.detail-hero {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 22px;
}

.avatar-mark {
  display: grid;
  width: 60px;
  height: 60px;
  flex: 0 0 auto;
  place-items: center;
  color: #fff;
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, $color-primary, #0f766e);
  border-radius: $radius-lg;
}

.detail-summary {
  min-width: 0;

  p {
    margin-top: 8px;
    color: $text-secondary;
    font-size: 13px;
  }
}

.detail-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;

  h2 {
    font-size: 24px;
    font-weight: 800;
    line-height: 1.2;
  }
}

.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
}

.detail-panel {
  padding: 18px;
}

.section-heading {
  margin-bottom: 14px;

  h3 {
    font-size: 16px;
    font-weight: 700;
  }
}

.detail-table {
  width: 100%;
}

@media (max-width: 720px) {
  .detail-hero {
    align-items: flex-start;
  }
}
</style>
