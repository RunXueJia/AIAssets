<template>
  <div class="records-page page-shell">
    <div class="page-heading">
      <div>
        <h2>生成记录</h2>
        <p>跟踪路线生成任务状态、耗时和处理结果。</p>
      </div>
    </div>

    <div class="search-bar">
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 140px" @change="search">
        <el-option label="等待中" value="pending" />
        <el-option label="生成中" value="streaming" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
        <el-option label="已取消" value="canceled" />
      </el-select>
      <el-select v-model="transportFilter" placeholder="交通方式" clearable style="width: 140px" @change="search">
        <el-option label="自驾" value="driving" />
        <el-option label="公共交通" value="transit" />
        <el-option label="步行" value="walking" />
        <el-option label="骑行" value="cycling" />
        <el-option label="摩托车" value="motorcycle" />
        <el-option label="混合出行" value="mixed" />
      </el-select>
      <el-input
        v-model="userKeyword"
        placeholder="搜索用户名"
        clearable
        style="width: 200px"
        @keyup.enter="search"
      />
      <el-button type="primary" @click="search">查询</el-button>
    </div>

    <div class="table-panel">
      <el-table :data="records" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="record_no" label="编号" min-width="150" show-overflow-tooltip />
        <el-table-column prop="user_nickname" label="用户" min-width="110" show-overflow-tooltip />
        <el-table-column label="路线" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.origin_text }} → {{ row.destination_text }}
          </template>
        </el-table-column>
        <el-table-column label="交通方式" width="110">
          <template #default="{ row }">{{ transportLabel(row.transport_mode) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时" width="90">
          <template #default="{ row }">
            {{ row.duration_ms ? `${(row.duration_ms / 1000).toFixed(1)}s` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="170" show-overflow-tooltip />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="$router.push(`/records/${row.id}`)">详情</el-button>
            <el-button
              v-if="row.status === 'failed'"
              text
              type="warning"
              @click="handleRetry(row)"
            >重试</el-button>
            <el-popconfirm title="确认删除该记录？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button text type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无生成记录" />
        </template>
      </el-table>
    </div>

    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :total="total"
        :page-size="pageSize"
        layout="total, prev, pager, next"
        @current-change="fetchRecords"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import { useLoading } from '@/composables/useLoading'

const { loading, withLoading } = useLoading()
const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const statusFilter = ref('')
const transportFilter = ref('')
const userKeyword = ref('')

const statusMap = { pending: '等待中', streaming: '生成中', completed: '已完成', failed: '失败', canceled: '已取消' }
const statusTypeMap = { pending: 'info', streaming: 'warning', completed: 'success', failed: 'danger', canceled: 'info' }
const transportMap = { driving: '自驾', transit: '公共交通', walking: '步行', cycling: '骑行', motorcycle: '摩托车', mixed: '混合出行' }

function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function transportLabel(t) { return transportMap[t] || t }

const fetchRecords = withLoading(async () => {
  const params = { page: page.value, page_size: pageSize }
  if (statusFilter.value) params.status = statusFilter.value
  if (transportFilter.value) params.transport_mode = transportFilter.value
  if (userKeyword.value) params.user_keyword = userKeyword.value
  const res = await adminApi.getRecords(params)
  records.value = res.data?.items || []
  total.value = res.data?.total || 0
})

function search() {
  page.value = 1
  fetchRecords()
}

async function handleRetry(row) {
  try {
    await adminApi.retryRecord(row.id)
    ElMessage.success('已创建重试任务')
    fetchRecords()
  } catch { /* ignore */ }
}

async function handleDelete(row) {
  try {
    await adminApi.deleteRecord(row.id)
    ElMessage.success('已删除')
    fetchRecords()
  } catch { /* ignore */ }
}

onMounted(() => fetchRecords())
</script>

<style lang="scss" scoped>
.records-page {
  max-width: 1360px;
}
</style>
