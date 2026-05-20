<template>
  <div class="source-list">
    <page-header title="素材来源" />

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="(label, value) in SOURCE_STATUS" :key="value" :label="label" :value="value" />
          </el-select>
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
        <el-table-column prop="site_name" label="来源网站" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <status-tag :status="row.status" :map="SOURCE_STATUS" />
          </template>
        </el-table-column>
        <el-table-column prop="published_at" label="发布时间" width="170" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openUrl(row.url)">查看原文</el-button>
            <el-button v-if="row.status === 'usable'" size="small" type="danger" link @click="markUnsuitable(row)">标记不适合</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size" :total="pagination.total" layout="total, prev, pager, next" @change="fetchList" />
      </div>
    </el-card>

    <!-- Summary detail drawer -->
    <el-drawer v-model="drawerVisible" title="素材汇总详情" size="500px">
      <template v-if="summary">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="汇总标题">{{ summary.title }}</el-descriptions-item>
          <el-descriptions-item label="内容摘要">{{ summary.summary }}</el-descriptions-item>
          <el-descriptions-item label="来源总数">{{ summary.source_count }}</el-descriptions-item>
          <el-descriptions-item label="可用来源">{{ summary.usable_source_count }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="summary.key_points && summary.key_points.length" class="section">
          <h4>关键要点</h4>
          <ul>
            <li v-for="(p, i) in summary.key_points" :key="i">{{ p }}</li>
          </ul>
        </div>
        <div v-if="summary.risk_notes && summary.risk_notes.length" class="section">
          <h4>风险提示</h4>
          <ul>
            <li v-for="(r, i) in summary.risk_notes" :key="i" style="color: #e6a23c">{{ r }}</li>
          </ul>
        </div>
        <el-alert v-if="summary.need_human_confirm" title="需要人工确认" type="warning" show-icon :closable="false" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getSourceList, getSummaryDetail, markSourceStatus } from '@/api/source'
import { SOURCE_STATUS } from '@/utils/constants'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'

const loading = ref(false)
const tableData = ref([])
const drawerVisible = ref(false)
const summary = ref(null)

const filters = reactive({ status: '' })

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

async function fetchList() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    if (filters.status) params.status = filters.status
    const data = await getSourceList(params)
    tableData.value = data.items || []
    pagination.total = data.total || 0
  } catch {}
  loading.value = false
}

function resetFilters() {
  filters.status = ''
  pagination.page = 1
  fetchList()
}

function openUrl(url) {
  if (url) window.open(url, '_blank')
}

async function markUnsuitable(row) {
  try {
    await markSourceStatus(row.id, 'not_suitable', '运营标记为不适合使用')
    row.status = 'not_suitable'
  } catch {}
}

onMounted(() => fetchList())
</script>

<style scoped lang="scss">
.filter-card { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
.section { margin-top: 20px; }
.section h4 { font-size: 14px; color: #303133; margin-bottom: 8px; }
.section ul { padding-left: 20px; }
.section li { font-size: 13px; color: #606266; line-height: 1.8; }
</style>
