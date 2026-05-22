<template>
  <div class="dashboard-page">
    <h3 class="page-title">首页</h3>
    <el-row :gutter="20">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">{{ stats.userCount }}</div>
          <div class="stat-label">总用户数</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">{{ stats.recordCount }}</div>
          <div class="stat-label">生成记录</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">{{ stats.enabledLlmCount }}</div>
          <div class="stat-label">已启用 LLM 配置</div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { adminApi } from '@/api/admin'

const stats = reactive({ userCount: '-', recordCount: '-', enabledLlmCount: '-' })

onMounted(async () => {
  try {
    const [userRes, recordRes, llmRes] = await Promise.all([
      adminApi.getUsers({ page: 1, page_size: 1 }),
      adminApi.getRecords({ page: 1, page_size: 1 }),
      adminApi.getLlmConfigs({ status: 'enabled', page: 1, page_size: 1 }),
    ])
    stats.userCount = userRes.data?.total || 0
    stats.recordCount = recordRes.data?.total || 0
    stats.enabledLlmCount = llmRes.data?.total || 0
  } catch { /* ignore */ }
})
</script>

<style lang="scss" scoped>
.page-title {
  font-size: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: $content-bg;
  border-radius: 8px;
  padding: 28px 24px;
  text-align: center;
  border: 1px solid $border-light;
}

.stat-value {
  font-size: 36px;
  font-weight: 600;
  color: $color-primary;
}

.stat-label {
  font-size: 13px;
  color: $text-secondary;
  margin-top: 8px;
}
</style>
