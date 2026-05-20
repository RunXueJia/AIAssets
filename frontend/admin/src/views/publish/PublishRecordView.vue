<template>
  <div class="publish-record">
    <page-header title="发布记录">
      <template #actions>
        <el-button type="primary" @click="openCreate">新增发布记录</el-button>
      </template>
    </page-header>

    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="内容标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="平台" width="120">
          <template #default="{ row }">{{ PLATFORMS[row.platform] || row.platform }}</template>
        </el-table-column>
        <el-table-column prop="platform_url" label="平台链接" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <a v-if="row.platform_url" :href="row.platform_url" target="_blank">{{ row.platform_url }}</a>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="published_at" label="发布时间" width="170" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
              {{ PUBLISH_STATUS[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="操作人" width="100" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size" :total="pagination.total" layout="total, prev, pager, next" @change="fetchList" />
      </div>
    </el-card>

    <!-- Create/Edit dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑发布记录' : '新增发布记录'" width="550px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="发布平台" prop="platform">
          <el-select v-model="form.platform" style="width: 100%">
            <el-option v-for="(label, value) in PLATFORMS" :key="value" :label="label" :value="value" />
          </el-select>
        </el-form-item>
        <el-form-item label="平台链接">
          <el-input v-model="form.platform_url" placeholder="粘贴发布后的链接" />
        </el-form-item>
        <el-form-item label="发布时间" prop="published_at">
          <el-date-picker v-model="form.published_at" type="datetime" format="YYYY-MM-DD HH:mm:ss" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option v-for="(label, value) in PUBLISH_STATUS" :key="value" :label="label" :value="value" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
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
import { createRecord, updateRecord, getRecordList } from '@/api/publish'
import { PLATFORMS, PUBLISH_STATUS } from '@/utils/constants'
import PageHeader from '@/components/common/PageHeader.vue'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref('')
const formRef = ref(null)

const form = reactive({
  platform: 'douyin',
  platform_url: '',
  published_at: '',
  status: 'published',
  remark: '',
  package_id: '',
})

const rules = {
  platform: [{ required: true, message: '请选择发布平台', trigger: 'change' }],
  published_at: [{ required: true, message: '请选择发布时间', trigger: 'change' }],
}

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

async function fetchList() {
  loading.value = true
  try {
    const data = await getRecordList({ page: pagination.page, page_size: pagination.page_size })
    tableData.value = data.items || []
    pagination.total = data.total || 0
  } catch {}
  loading.value = false
}

function openCreate() {
  isEdit.value = false
  editId.value = ''
  form.platform = 'douyin'
  form.platform_url = ''
  form.published_at = ''
  form.status = 'published'
  form.remark = ''
  form.package_id = ''
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  editId.value = row.id
  form.platform = row.platform
  form.platform_url = row.platform_url || ''
  form.published_at = row.published_at || ''
  form.status = row.status
  form.remark = row.remark || ''
  form.package_id = row.package_id || ''
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    const params = { ...form }
    if (isEdit.value) {
      params.record_id = editId.value
      await updateRecord(params)
    } else {
      await createRecord(params)
    }
    dialogVisible.value = false
    fetchList()
  } catch {}
}

onMounted(() => fetchList())
</script>

<style scoped lang="scss">
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
