<template>
  <div class="dashboard-page page-shell">
    <div class="page-heading">
      <div>
        <h2>控制台概览</h2>
        <p>查看后台核心资源的当前规模。</p>
      </div>
    </div>

    <el-alert
      v-if="errorText"
      :title="errorText"
      type="warning"
      show-icon
      :closable="false"
    />

    <div class="stat-grid" v-loading="dashboardLoading">
      <article
        v-for="item in statItems"
        :key="item.key"
        class="stat-card"
        :class="item.key"
      >
        <div class="stat-meta">
          <span class="stat-label">{{ item.label }}</span>
          <span class="stat-chip">{{ item.scope }}</span>
        </div>
        <div class="stat-value">{{ item.value }}</div>
        <div class="stat-note">{{ item.note }}</div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'

const stats = reactive({ userCount: '-', recordCount: '-', enabledLlmCount: '-' })
const dashboardLoading = ref(false)
const errorText = ref('')

const statItems = computed(() => [
  {
    key: 'users',
    label: '总用户数',
    value: stats.userCount,
    scope: 'Users',
    note: '包含所有后台可检索用户',
  },
  {
    key: 'records',
    label: '生成记录',
    value: stats.recordCount,
    scope: 'Records',
    note: '累计生成任务记录',
  },
  {
    key: 'llm',
    label: '已启用 LLM 配置',
    value: stats.enabledLlmCount,
    scope: 'LLM',
    note: '当前可用的模型配置数',
  },
])

onMounted(async () => {
  dashboardLoading.value = true
  errorText.value = ''
  try {
    const [userRes, recordRes, llmRes] = await Promise.all([
      adminApi.getUsers({ page: 1, page_size: 1 }),
      adminApi.getRecords({ page: 1, page_size: 1 }),
      adminApi.getLlmConfigs({ status: 'enabled', page: 1, page_size: 1 }),
    ])
    stats.userCount = userRes.data?.total || 0
    stats.recordCount = recordRes.data?.total || 0
    stats.enabledLlmCount = llmRes.data?.total || 0
  } catch {
    errorText.value = '概览数据暂时不可用，请稍后刷新。'
  } finally {
    dashboardLoading.value = false
  }
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  max-width: 1180px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  min-height: 172px;
}

.stat-card {
  position: relative;
  min-height: 172px;
  padding: 22px;
  overflow: hidden;
  background: $content-bg;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  box-shadow: $shadow-card;

  &::after {
    position: absolute;
    right: -32px;
    bottom: -44px;
    width: 132px;
    height: 132px;
    content: "";
    background: rgba(37, 99, 235, 0.08);
    border-radius: 999px;
  }

  &.records::after {
    background: rgba(15, 118, 110, 0.1);
  }

  &.llm::after {
    background: rgba(217, 119, 6, 0.12);
  }
}

.stat-meta {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.stat-value {
  position: relative;
  z-index: 1;
  margin-top: 24px;
  color: $text-primary;
  font-size: 42px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: 0;
}

.stat-label {
  color: $text-secondary;
  font-size: 13px;
  font-weight: 700;
}

.stat-chip {
  color: $color-primary;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
  background: $surface-strong;
  border-radius: 999px;
}

.stat-note {
  position: relative;
  z-index: 1;
  margin-top: 18px;
  color: $text-muted;
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 980px) {
  .stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
