<template>
  <div class="task-list">
    <page-header title="生成任务">
      <template #actions>
        <el-button type="primary" @click="$router.push('/generation/create')">新建生成任务</el-button>
      </template>
    </page-header>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="(label, value) in TASK_STATUS" :key="value" :label="label" :value="value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索方向、主题" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="任务编号" width="120" />
        <el-table-column prop="direction" label="内容方向" min-width="200" show-overflow-tooltip />
        <el-table-column prop="topic" label="主题" width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <status-tag :status="row.status" :map="TASK_STATUS" />
          </template>
        </el-table-column>
        <el-table-column label="当前阶段" width="140">
          <template #default="{ row }">
            {{ STAGE_NAMES[row.current_stage] || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="进度" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :stroke-width="8" :show-text="false" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="router.push(`/generation/process/${row.id}`)">详情</el-button>
            <el-button v-if="row.status === 'running' || row.status === 'pending'" size="small" type="warning" link @click="handleCancel(row)">取消</el-button>
            <el-button v-if="row.status === 'failed'" size="small" type="primary" link @click="handleRetry(row)">重试</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size" :total="pagination.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" @change="fetchList" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { getTaskList, cancelTask, retryTask } from '@/api/generation'
import { TASK_STATUS, STAGE_NAMES } from '@/utils/constants'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])

const filters = reactive({
  status: '',
  keyword: '',
  dateRange: null,
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

async function fetchList() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    if (filters.status) params.status = filters.status
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.dateRange) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    const data = await getTaskList(params)
    tableData.value = data.items || []
    pagination.total = data.total || 0
  } catch {}
  loading.value = false
}

function resetFilters() {
  filters.status = ''
  filters.keyword = ''
  filters.dateRange = null
  pagination.page = 1
  fetchList()
}

async function handleCancel(row) {
  try {
    await ElMessageBox.confirm('确定取消此任务？', '提示', { type: 'warning' })
    await cancelTask(row.id)
    row.status = 'cancelled'
  } catch {}
}

async function handleRetry(row) {
  try {
    await retryTask(row.id, row.current_stage)
    router.push(`/generation/process/${row.id}`)
  } catch {}
}

onMounted(() => fetchList())
</script>

<style scoped lang="scss">
.filter-card {
  margin-bottom: 16px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
