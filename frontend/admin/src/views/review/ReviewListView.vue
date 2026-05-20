<template>
  <div class="review-list">
    <page-header title="内容审核" />

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="(label, value) in CONTENT_STATUS" :key="value" :label="label" :value="value" />
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
        <el-table-column prop="title" label="内容标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="content_type" label="类型" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <status-tag :status="row.status" :map="CONTENT_STATUS" />
          </template>
        </el-table-column>
        <el-table-column label="需人工确认" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.need_human_confirm" type="warning" size="small">需要确认</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="创建人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending_review'">
              <el-button size="small" type="success" @click="handleApprove(row)">通过</el-button>
              <el-button size="small" type="warning" @click="handleEditApprove(row)">修改后通过</el-button>
              <el-button size="small" type="danger" @click="handleReject(row)">驳回</el-button>
            </template>
            <el-button v-if="row.status === 'rejected'" size="small" type="primary" @click="handleRegenerate(row)">重新生成</el-button>
            <el-button size="small" type="primary" link @click="goToContent(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size" :total="pagination.total" layout="total, prev, pager, next" @change="fetchList" />
      </div>
    </el-card>

    <!-- Reject dialog -->
    <el-dialog v-model="rejectVisible" title="驳回内容" width="450px">
      <el-form>
        <el-form-item label="驳回原因" required>
          <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请填写驳回原因，以便重新生成时参考" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :disabled="!rejectReason" @click="confirmReject">确认驳回</el-button>
      </template>
    </el-dialog>

    <!-- Regenerate dialog -->
    <el-dialog v-model="regenerateVisible" title="重新生成" width="450px">
      <el-form>
        <el-form-item label="调整要求">
          <el-input v-model="regenerateReason" type="textarea" :rows="3" placeholder="请描述需要调整的方向" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="regenerateVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRegenerate">确认重新生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { getReviewList, approve, approveWithEdit, reject, regenerate } from '@/api/review'
import { CONTENT_STATUS } from '@/utils/constants'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])

const filters = reactive({ status: '', keyword: '' })
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const rejectVisible = ref(false)
const rejectReason = ref('')
let rejectTarget = null

const regenerateVisible = ref(false)
const regenerateReason = ref('')
let regenerateTarget = null

async function fetchList() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    if (filters.status) params.status = filters.status
    if (filters.keyword) params.keyword = filters.keyword
    const data = await getReviewList(params)
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

async function handleApprove(row) {
  try {
    await ElMessageBox.confirm('确认通过审核？通过后将进入合成队列。', '确认通过', { type: 'success' })
    await approve(row.content_id, row.content_type, '')
    row.status = 'approved'
  } catch {}
}

function handleEditApprove(row) {
  router.push(`/script/detail/${row.content_id}`)
}

function handleReject(row) {
  rejectTarget = row
  rejectReason.value = ''
  rejectVisible.value = true
}

async function confirmReject() {
  if (!rejectTarget || !rejectReason.value) return
  try {
    await reject(rejectTarget.content_id, rejectTarget.content_type, rejectReason.value)
    rejectTarget.status = 'rejected'
    rejectVisible.value = false
  } catch {}
}

function handleRegenerate(row) {
  regenerateTarget = row
  regenerateReason.value = ''
  regenerateVisible.value = true
}

async function confirmRegenerate() {
  if (!regenerateTarget) return
  try {
    const result = await regenerate(regenerateTarget.content_id, regenerateTarget.content_type, regenerateReason.value)
    regenerateVisible.value = false
    router.push(`/generation/process/${result.task_id}`)
  } catch {}
}

function goToContent(row) {
  if (row.content_type === 'script') {
    router.push(`/script/detail/${row.content_id}`)
  }
}

onMounted(() => fetchList())
</script>

<style scoped lang="scss">
.filter-card { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
