<template>
  <div class="monitor-list">
    <page-header title="话题监控">
      <template #actions>
        <el-button type="primary" @click="openCreate">新建监控任务</el-button>
      </template>
    </page-header>

    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="topic" label="监控话题" min-width="180" />
        <el-table-column prop="audience" label="关注人群" width="120" />
        <el-table-column prop="schedule_time" label="每天更新时间" width="120" />
        <el-table-column prop="fetch_limit" label="抓取上限" width="90" />
        <el-table-column label="自动生成选题" width="120">
          <template #default="{ row }">
            <el-tag :type="row.auto_generate_topics ? 'success' : 'info'" size="small">
              {{ row.auto_generate_topics ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <status-tag :status="row.status" :map="MONITOR_STATUS" />
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="最后运行" width="170" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button v-if="row.status === 'enabled'" size="small" type="warning" link @click="changeStatus(row, 'paused')">暂停</el-button>
            <el-button v-if="row.status === 'paused'" size="small" type="success" link @click="changeStatus(row, 'enabled')">恢复</el-button>
            <el-button size="small" type="danger" link @click="changeStatus(row, 'deleted')">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size" :total="pagination.total" layout="total, prev, pager, next" @change="fetchList" />
      </div>
    </el-card>

    <!-- Create/Edit dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑监控任务' : '新建监控任务'" width="550px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="130px">
        <el-form-item label="监控的话题" prop="topic">
          <el-input v-model="form.topic" placeholder="例如：AI 办公工具更新" />
        </el-form-item>
        <el-form-item label="主要关注的人群">
          <el-input v-model="form.audience" placeholder="例如：普通职场人" />
        </el-form-item>
        <el-form-item label="每天什么时候更新" prop="schedule_time">
          <el-time-picker v-model="form.schedule_time" format="HH:mm" value-format="HH:mm" placeholder="选择时间" />
        </el-form-item>
        <el-form-item label="每次最多抓取多少条">
          <el-input-number v-model="form.fetch_limit" :min="5" :max="100" />
        </el-form-item>
        <el-form-item label="是否自动生成选题">
          <el-switch v-model="form.auto_generate_topics" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { createMonitor, getMonitorList, updateMonitor, changeMonitorStatus } from '@/api/monitor'
import { MONITOR_STATUS } from '@/utils/constants'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref('')
const formRef = ref(null)

const form = reactive({
  topic: '',
  audience: '',
  schedule_time: '09:00',
  fetch_limit: 20,
  auto_generate_topics: true,
})

const rules = {
  topic: [{ required: true, message: '请输入监控的话题', trigger: 'blur' }],
  schedule_time: [{ required: true, message: '请选择更新时间', trigger: 'change' }],
}

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

async function fetchList() {
  loading.value = true
  try {
    const data = await getMonitorList({ page: pagination.page, page_size: pagination.page_size })
    tableData.value = data.items || []
    pagination.total = data.total || 0
  } catch {}
  loading.value = false
}

function openCreate() {
  isEdit.value = false
  editId.value = ''
  form.topic = ''
  form.audience = ''
  form.schedule_time = '09:00'
  form.fetch_limit = 20
  form.auto_generate_topics = true
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  editId.value = row.id
  form.topic = row.topic
  form.audience = row.audience
  form.schedule_time = row.schedule_time
  form.fetch_limit = row.fetch_limit
  form.auto_generate_topics = row.auto_generate_topics
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (isEdit.value) {
      await updateMonitor({ monitor_id: editId.value, ...form })
    } else {
      await createMonitor({ ...form })
    }
    dialogVisible.value = false
    fetchList()
  } catch {}
}

async function changeStatus(row, status) {
  const labels = { deleted: '删除', paused: '暂停' }
  if (status === 'deleted') {
    try { await ElMessageBox.confirm('确定删除此监控任务？', '确认删除', { type: 'warning' }) } catch { return }
  }
  try {
    await changeMonitorStatus(row.id, status)
    row.status = status
  } catch {}
}

onMounted(() => fetchList())
</script>

<style scoped lang="scss">
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
