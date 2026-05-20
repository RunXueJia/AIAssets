<template>
  <div class="report-list">
    <page-header title="每日报告" />

    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="title" label="报告标题" min-width="220" />
        <el-table-column prop="generation_task_count" label="生成任务" width="90" />
        <el-table-column prop="script_count" label="脚本" width="70" />
        <el-table-column prop="video_count" label="视频" width="70" />
        <el-table-column prop="package_count" label="发布包" width="80" />
        <el-table-column prop="failed_task_count" label="失败任务" width="90" />
        <el-table-column prop="created_at" label="生成时间" width="170" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="$router.push(`/report/detail/${row.id}`)">详情</el-button>
            <el-button size="small" type="success" link @click="exportReport(row, 'markdown')">导出</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size" :total="pagination.total" layout="total, prev, pager, next" @change="fetchList" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getDailyReportList, getReportExportUrl } from '@/api/report'
import PageHeader from '@/components/common/PageHeader.vue'

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

async function fetchList() {
  loading.value = true
  try {
    const data = await getDailyReportList({ page: pagination.page, page_size: pagination.page_size })
    tableData.value = data.items || []
    pagination.total = data.total || 0
  } catch {}
  loading.value = false
}

function exportReport(row, format) {
  const token = localStorage.getItem('token')
  const url = getReportExportUrl(row.id, format)
  const a = document.createElement('a')
  a.href = `${url}?token=${token}`
  a.download = ''
  a.click()
}

onMounted(() => fetchList())
</script>

<style scoped lang="scss">
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
