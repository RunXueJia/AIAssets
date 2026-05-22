<template>
  <div class="user-detail" v-loading="loading">
    <div class="back-bar">
      <el-button text @click="$router.push('/users')">
        <el-icon><ArrowLeft /></el-icon> 返回用户列表
      </el-button>
    </div>

    <template v-if="detail">
      <h3>用户详情</h3>
      <el-descriptions :column="2" border class="detail-table">
        <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ detail.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ detail.nickname }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ detail.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag size="small">{{ roleLabel(detail.role) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="detail.status === 'active' ? 'success' : 'danger'" size="small">
            {{ detail.status === 'active' ? '正常' : '已禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="生成次数">{{ detail.generation_count }}</el-descriptions-item>
        <el-descriptions-item label="最后登录">{{ detail.last_login_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ detail.created_at }}</el-descriptions-item>
      </el-descriptions>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { adminApi } from '@/api/admin'
import { useLoading } from '@/composables/useLoading'

const route = useRoute()
const { loading, withLoading } = useLoading()
const detail = ref(null)

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
.back-bar { margin-bottom: 16px; }
h3 { margin-bottom: 20px; }
.detail-table { max-width: 720px; }
</style>
