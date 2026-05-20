<template>
  <div class="topic-list">
    <page-header title="选题管理" />

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="(label, value) in TOPIC_STATUS" :key="value" :label="label" :value="value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索标题" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="audience" label="受众" width="120" />
        <el-table-column prop="column" label="栏目" width="140" />
        <el-table-column prop="duration_seconds" label="时长(秒)" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <status-tag :status="row.status" :map="TOPIC_STATUS" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="$router.push(`/topic/detail/${row.id}`)">详情</el-button>
            <el-button v-if="row.status === 'draft'" size="small" type="success" link @click="changeStatus(row, 'approved')">通过</el-button>
            <el-button v-if="row.status === 'draft'" size="small" type="danger" link @click="changeStatus(row, 'rejected')">驳回</el-button>
            <el-button size="small" type="primary" link @click="generate(row)">生成脚本</el-button>
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
import { useRouter } from 'vue-router'
import { getTopicList, changeTopicStatus, generateScript } from '@/api/topic'
import { TOPIC_STATUS } from '@/utils/constants'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])

const filters = reactive({ status: '', keyword: '' })
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

async function fetchList() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    if (filters.status) params.status = filters.status
    if (filters.keyword) params.keyword = filters.keyword
    const data = await getTopicList(params)
    tableData.value = data.items || []
    pagination.total = data.total || 0
  } catch {}
  loading.value = false
}

function resetFilters() {
  filters.status = ''
  filters.keyword = ''
  pagination.page = 1
  fetchList()
}

async function changeStatus(row, status) {
  try {
    await changeTopicStatus(row.id, status, '')
    row.status = status
  } catch {}
}

async function generate(row) {
  try {
    const result = await generateScript(row.id, 'now')
    router.push(`/generation/process/${result.task_id}`)
  } catch {}
}

onMounted(() => fetchList())
</script>

<style scoped lang="scss">
.filter-card { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
