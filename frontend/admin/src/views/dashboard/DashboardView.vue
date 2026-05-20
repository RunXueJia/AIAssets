<template>
  <div class="dashboard">
    <page-header title="首页概览" />

    <!-- Stat cards -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="4" v-for="stat in stats" :key="stat.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Trend chart -->
    <el-card class="trend-card">
      <template #header>
        <div class="card-header">
          <span>产出趋势</span>
          <el-radio-group v-model="range" size="small" @change="fetchTrend">
            <el-radio-button value="today">今日</el-radio-button>
            <el-radio-button value="7d">近7天</el-radio-button>
            <el-radio-button value="30d">近30天</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>

    <!-- Success rates -->
    <el-row :gutter="16" class="rate-row">
      <el-col :span="6" v-for="rate in rates" :key="rate.label">
        <el-card shadow="hover">
          <div class="rate-card">
            <div class="rate-label">{{ rate.label }}</div>
            <el-progress :percentage="rate.value" :color="rate.color" :stroke-width="16" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { getOverview, getTrend } from '@/api/dashboard'
import PageHeader from '@/components/common/PageHeader.vue'

const range = ref('7d')
const chartRef = ref(null)
let chart = null

const stats = reactive([
  { label: '生成任务', value: 0 },
  { label: '抓取素材', value: 0 },
  { label: '新增选题', value: 0 },
  { label: '新增脚本', value: 0 },
  { label: '合成视频', value: 0 },
  { label: '待审核', value: 0 },
  { label: '合成失败', value: 0 },
  { label: '发布包', value: 0 },
  { label: '抓取任务', value: 0 },
])

const rates = reactive([
  { label: '任务成功率', value: 0, color: '#67c23a' },
  { label: '抓取成功率', value: 0, color: '#409eff' },
  { label: 'LLM 成功率', value: 0, color: '#e6a23c' },
  { label: 'SSE 中断率', value: 0, color: '#f56c6c' },
])

async function fetchOverview() {
  try {
    const data = await getOverview()
    stats[0].value = data.generation_task_count || 0
    stats[1].value = data.source_item_count || 0
    stats[2].value = data.topic_count || 0
    stats[3].value = data.script_count || 0
    stats[4].value = data.video_count || 0
    stats[5].value = data.pending_review_count || 0
    stats[6].value = data.render_failed_count || 0
    stats[7].value = data.package_count || 0
    stats[8].value = data.fetch_task_count || 0
  } catch {}
}

async function fetchTrend() {
  try {
    const data = await getTrend(range.value)
    rates[0].value = Math.round((data.task_success_rate || 0) * 100)
    rates[1].value = Math.round((data.fetch_success_rate || 0) * 100)
    rates[2].value = Math.round((data.llm_success_rate || 0) * 100)
    rates[3].value = Math.round((data.sse_disconnect_rate || 0) * 100)
    renderChart(data)
  } catch {}
}

function renderChart(data) {
  if (!chart) return
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['生成任务', '素材', '脚本', '视频'] },
    xAxis: { type: 'category', data: data.dates || [] },
    yAxis: { type: 'value' },
    series: [
      { name: '生成任务', type: 'line', data: data.generation_task_counts || [], smooth: true },
      { name: '素材', type: 'line', data: data.source_item_counts || [], smooth: true },
      { name: '脚本', type: 'line', data: data.script_counts || [], smooth: true },
      { name: '视频', type: 'line', data: data.video_counts || [], smooth: true },
    ],
  })
}

onMounted(async () => {
  await Promise.all([fetchOverview(), fetchTrend()])
  await nextTick()
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    fetchTrend()
  }
})

onUnmounted(() => {
  chart?.dispose()
})
</script>

<style scoped lang="scss">
.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  cursor: default;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.trend-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 320px;
}

.rate-row {
  margin-bottom: 16px;
}

.rate-card {
  text-align: center;
}

.rate-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}
</style>
