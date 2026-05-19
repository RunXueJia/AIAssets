<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">
          任务与日报
        </h1>
        <p class="page-subtitle">
          查看调度任务、失败原因和每日运营报告。
        </p>
      </div>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane
        label="任务日志"
        name="tasks"
      >
        <DataPanel
          :items="tasks.items"
          :total="tasks.total"
          :loading="loading"
          @search="load"
        >
          <el-table-column
            prop="task_type"
            label="任务类型"
            min-width="180"
          />
          <el-table-column
            prop="duration_ms"
            label="耗时 ms"
            width="120"
          />
          <el-table-column
            label="状态"
            width="120"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>
      <el-tab-pane
        label="每日报告"
        name="reports"
      >
        <DataPanel
          :items="reports.items"
          :total="reports.total"
          :loading="loading"
          @search="load"
        >
          <el-table-column
            prop="date"
            label="日期"
            width="140"
          />
          <el-table-column
            prop="summary"
            label="摘要"
            min-width="260"
          />
          <el-table-column
            label="状态"
            width="120"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="120"
          >
            <template #default="{ row }">
              <el-button
                text
                type="primary"
                @click="openReport(row)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>
    </el-tabs>

    <el-drawer
      v-model="reportVisible"
      title="日报详情"
      size="620"
    >
      <pre class="report-body">{{ reportDetail.markdown }}</pre>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'

import DataPanel from '@/components/DataPanel.vue'
import StatusTag from '@/components/StatusTag.vue'
import { reportApi } from '@/api'

const tab = ref('tasks')
const loading = ref(false)
const tasks = reactive({ items: [], total: 0 })
const reports = reactive({ items: [], total: 0 })
const reportVisible = ref(false)
const reportDetail = ref({})

async function load(keyword = '') {
  loading.value = true
  try {
    if (tab.value === 'tasks') {
      const data = await reportApi.getTasks({ keyword })
      tasks.items = data.items
      tasks.total = data.total
    } else {
      const data = await reportApi.getReports({ keyword })
      reports.items = data.items
      reports.total = data.total
    }
  } finally {
    loading.value = false
  }
}

async function openReport(row) {
  reportDetail.value = await reportApi.getReportDetail(row.id)
  reportVisible.value = true
}

watch(tab, () => load())
onMounted(load)
</script>

<style scoped lang="scss">
.report-body {
  min-height: 360px;
  padding: 16px;
  border: 1px solid var(--h24-line);
  border-radius: 8px;
  background: #f8fbfb;
  font-family: "Microsoft YaHei", sans-serif;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
