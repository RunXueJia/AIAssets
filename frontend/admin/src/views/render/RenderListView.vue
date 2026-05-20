<template>
  <div class="render-list">
    <page-header title="视频合成" />

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="(label, value) in RENDER_STATUS" :key="value" :label="label" :value="value" />
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
        <el-table-column prop="title" label="视频标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <status-tag :status="row.status" :map="RENDER_STATUS" />
          </template>
        </el-table-column>
        <el-table-column label="进度" width="140">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :stroke-width="8" :status="row.status === 'failed' ? 'exception' : undefined" />
          </template>
        </el-table-column>
        <el-table-column prop="duration_seconds" label="时长(秒)" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'success' && row.video_id" size="small" type="primary" link @click="previewVideo(row)">预览</el-button>
            <el-button v-if="row.status === 'failed'" size="small" type="primary" link @click="handleRetry(row)">重试合成</el-button>
            <el-button v-if="row.error_message" size="small" type="danger" link @click="showError(row)">查看原因</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size" :total="pagination.total" layout="total, prev, pager, next" @change="fetchList" />
      </div>
    </el-card>

    <!-- Video preview dialog -->
    <el-dialog v-model="previewVisible" title="视频预览" width="480px">
      <div v-if="previewUrl" class="video-preview">
        <video :src="previewUrl" controls style="width: 100%; max-height: 70vh" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { getRenderList, retryRender, getVideoDetail } from '@/api/render'
import { RENDER_STATUS } from '@/utils/constants'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { previewVideoUrl } from '@/api/file'

const loading = ref(false)
const tableData = ref([])
const previewVisible = ref(false)
const previewUrl = ref('')

const filters = reactive({ status: '' })
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

async function fetchList() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    if (filters.status) params.status = filters.status
    const data = await getRenderList(params)
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

async function previewVideo(row) {
  try {
    const detail = await getVideoDetail(row.video_id)
    previewUrl.value = detail.preview_url || previewVideoUrl(row.video_id)
    previewVisible.value = true
  } catch {}
}

async function handleRetry(row) {
  try {
    await retryRender(row.id)
    row.status = 'pending'
    row.progress = 0
  } catch {}
}

function showError(row) {
  ElMessageBox.alert(row.error_message || '未知错误', '合成失败原因', { type: 'error' })
}

onMounted(() => fetchList())
</script>

<style scoped lang="scss">
.filter-card { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
