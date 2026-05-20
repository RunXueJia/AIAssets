<template>
  <div class="package-list">
    <page-header title="发布包管理" />

    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="video_id" label="关联视频" width="120" />
        <el-table-column label="平台" width="180">
          <template #default="{ row }">
            <el-tag v-for="p in row.platforms" :key="p" size="small" style="margin-right: 4px">
              {{ PLATFORMS[p] || p }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="文件大小" width="100">
          <template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="$router.push(`/package/detail/${row.id}`)">详情</el-button>
            <el-button size="small" type="success" link @click="downloadPackage(row)">下载</el-button>
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
import { getPackageList, getPackageDownloadUrl } from '@/api/package'
import { PLATFORMS } from '@/utils/constants'
import { formatFileSize } from '@/utils/format'
import PageHeader from '@/components/common/PageHeader.vue'

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

async function fetchList() {
  loading.value = true
  try {
    const data = await getPackageList({ page: pagination.page, page_size: pagination.page_size })
    tableData.value = data.items || []
    pagination.total = data.total || 0
  } catch {}
  loading.value = false
}

function downloadPackage(row) {
  const token = localStorage.getItem('token')
  const url = row.download_url || getPackageDownloadUrl(row.id)
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
