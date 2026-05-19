<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">
          今日看板
        </h1>
        <p class="page-subtitle">
          跟踪内容生产、访问下载、线索与任务成功率。
        </p>
      </div>
      <el-button
        type="primary"
        :icon="Refresh"
        @click="load"
      >
        刷新
      </el-button>
    </div>

    <div class="metric-grid">
      <div
        v-for="metric in metrics"
        :key="metric.label"
        class="metric-card surface"
      >
        <div class="metric-label">
          {{ metric.label }}
        </div>
        <div class="metric-value">
          {{ metric.value }}
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <section class="surface block">
        <h2>栏目表现</h2>
        <el-table
          :data="channelPerformance"
          border
        >
          <el-table-column
            prop="name"
            label="栏目"
            min-width="160"
          />
          <el-table-column
            prop="output_count"
            label="产出"
            width="90"
          />
          <el-table-column
            prop="visits"
            label="访问"
            width="100"
          />
          <el-table-column
            prop="leads"
            label="线索"
            width="90"
          />
        </el-table>
      </section>
      <section class="surface block">
        <h2>任务运行</h2>
        <el-table
          :data="taskMetrics"
          border
        >
          <el-table-column
            prop="task_type"
            label="任务类型"
            min-width="160"
          />
          <el-table-column
            label="成功率"
            width="110"
          >
            <template #default="{ row }">
              {{ Math.round(row.success_rate * 100) }}%
            </template>
          </el-table-column>
          <el-table-column
            prop="avg_duration_ms"
            label="平均耗时 ms"
            width="130"
          />
        </el-table>
      </section>
    </div>
  </div>
</template>

<script setup>
import { Refresh } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { dashboardApi } from '@/api'

const overview = ref({})
const channelPerformance = ref([])
const taskMetrics = ref([])

const metrics = computed(() => [
  { label: '选题', value: overview.value.topics_count || 0 },
  { label: '脚本', value: overview.value.scripts_count || 0 },
  { label: '视频', value: overview.value.videos_count || 0 },
  { label: '线索', value: overview.value.lead_count || 0 },
  { label: '访问', value: overview.value.visit_count || 0 },
  { label: '下载', value: overview.value.download_count || 0 },
  { label: '已发布', value: overview.value.published_count || 0 },
  { label: '任务成功率', value: `${Math.round((overview.value.task_success_rate || 0) * 100)}%` }
])

async function load() {
  const [overviewData, performanceData, metricsData] = await Promise.all([
    dashboardApi.getTodayOverview(),
    dashboardApi.getChannelPerformance(),
    dashboardApi.getTaskMetrics()
  ])
  overview.value = overviewData
  channelPerformance.value = normalizeRows(performanceData)
  taskMetrics.value = normalizeRows(metricsData)
}

function normalizeRows(data) {
  if (Array.isArray(data)) {
    return data
  }
  if (Array.isArray(data?.items)) {
    return data.items
  }
  return []
}

onMounted(load)
</script>

<style scoped lang="scss">
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.block {
  padding: 16px;

  h2 {
    margin: 0 0 14px;
    font-size: 18px;
  }
}
</style>
