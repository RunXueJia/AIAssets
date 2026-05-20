<template>
  <div class="daily-summary">
    <page-header title="每日汇总" />

    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="topic" label="监控话题" min-width="180" />
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="source_count" label="来源数量" width="100" />
        <el-table-column prop="topic_count" label="选题数量" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="生成时间" width="170" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="$router.push(`/source/summary/${row.summary_id}`)">查看素材</el-button>
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
import { getDailySummaryList } from '@/api/monitor'
import PageHeader from '@/components/common/PageHeader.vue'

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

async function fetchList() {
  loading.value = true
  try {
    const data = await getDailySummaryList({ page: pagination.page, page_size: pagination.page_size })
    tableData.value = data.items || []
    pagination.total = data.total || 0
  } catch {}
  loading.value = false
}

onMounted(() => fetchList())
</script>

<style scoped lang="scss">
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
