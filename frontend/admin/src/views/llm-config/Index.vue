<template>
  <div class="llm-config-page">
    <div class="page-header">
      <h3>LLM 配置管理</h3>
      <el-button type="primary" @click="openDialog('add')">添加配置</el-button>
    </div>

    <el-table :data="configs" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="provider" label="供应商" width="140" />
      <el-table-column label="API 地址" min-width="220">
        <template #default="{ row }">{{ row.base_url }}</template>
      </el-table-column>
      <el-table-column prop="model_name" label="模型" min-width="140" />
      <el-table-column label="API Key" width="140">
        <template #default="{ row }">{{ row.api_key_masked || '****' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" size="small">
            {{ row.status === 'enabled' ? '已启用' : '已停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="默认" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.is_default" type="warning" size="small">默认</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="测试状态" width="110">
        <template #default="{ row }">
          <el-tag v-if="row.last_test_status === 'success'" type="success" size="small">通过</el-tag>
          <el-tag v-else-if="row.last_test_status === 'failed'" type="danger" size="small">失败</el-tag>
          <span v-else style="color: #999">未测试</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="320" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openDialog('edit', row)">编辑</el-button>
          <el-button text type="success" @click="handleTest(row)">测试</el-button>
          <el-popconfirm
            v-if="row.status === 'enabled'"
            title="确认停用该配置？"
            @confirm="handleDisable(row)"
          >
            <template #reference>
              <el-button text type="warning">停用</el-button>
            </template>
          </el-popconfirm>
          <el-popconfirm
            v-else
            title="确认启用该配置？"
            @confirm="handleEnable(row)"
          >
            <template #reference>
              <el-button text type="success">启用</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '添加 LLM 配置' : '编辑 LLM 配置'"
      width="560px"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" label-width="110px">
        <el-form-item label="名称" prop="name" :rules="[{ required: true, message: '请输入名称' }]">
          <el-input v-model="form.name" placeholder="配置名称" />
        </el-form-item>
        <el-form-item label="供应商" prop="provider" :rules="[{ required: true, message: '请输入供应商' }]">
          <el-input v-model="form.provider" placeholder="例如 openai-compatible" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item label="API 地址" prop="base_url" :rules="[{ required: true, message: '请输入 API 地址' }]">
          <el-input v-model="form.base_url" placeholder="https://api.example.com/v1" />
        </el-form-item>
        <el-form-item label="模型名" prop="model_name" :rules="[{ required: true, message: '请输入模型名' }]">
          <el-input v-model="form.model_name" placeholder="gpt-4.1-mini" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="dialogMode === 'edit' ? '留空则不修改' : '输入 API Key'"
          />
        </el-form-item>
        <el-form-item label="超时 (秒)">
          <el-input-number v-model="form.timeout_s" :min="1" :max="300" />
        </el-form-item>
        <el-form-item label="最大 Token">
          <el-input-number v-model="form.max_tokens" :min="100" :max="100000" />
        </el-form-item>
        <el-form-item label="Temperature">
          <el-input-number v-model="form.temperature" :min="0" :max="2" :precision="1" :step="0.1" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- Test Dialog -->
    <el-dialog v-model="testVisible" title="测试 LLM 连接" width="480px">
      <el-form>
        <el-form-item label="测试 Prompt">
          <el-input v-model="testPrompt" type="textarea" :rows="3" placeholder="请回复 OK" />
        </el-form-item>
      </el-form>
      <div v-if="testResult" class="test-result" :class="testResult.status">
        <p><strong>状态：</strong>{{ testResult.status === 'success' ? '成功' : '失败' }}</p>
        <p><strong>响应：</strong>{{ testResult.message }}</p>
        <p v-if="testResult.duration_ms"><strong>耗时：</strong>{{ (testResult.duration_ms / 1000).toFixed(1) }}s</p>
        <p v-if="testResult.tested_at"><strong>测试时间：</strong>{{ testResult.tested_at }}</p>
      </div>
      <template #footer>
        <el-button @click="testVisible = false">关闭</el-button>
        <el-button type="primary" :loading="testing" @click="doTest">开始测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import { useLoading } from '@/composables/useLoading'

const { loading, withLoading } = useLoading()
const configs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const dialogVisible = ref(false)
const dialogMode = ref('add')
const submitting = ref(false)
const formRef = ref(null)
const editingId = ref(null)

const form = reactive({
  name: '',
  provider: 'openai-compatible',
  base_url: '',
  model_name: '',
  api_key: '',
  timeout_s: 60,
  max_tokens: 8000,
  temperature: 0.7,
  is_default: false,
})

const testVisible = ref(false)
const testing = ref(false)
const testPrompt = ref('请回复 OK')
const testResult = ref(null)
const testingId = ref(null)

const fetchConfigs = withLoading(async () => {
  const res = await adminApi.getLlmConfigs({ page: page.value, page_size: pageSize })
  configs.value = res.data?.items || []
  total.value = res.data?.total || 0
})

async function openDialog(mode, row) {
  dialogMode.value = mode
  if (mode === 'edit' && row) {
    editingId.value = row.id
    form.name = row.name
    form.provider = row.provider
    form.base_url = row.base_url
    form.model_name = row.model_name
    form.api_key = ''
    form.is_default = row.is_default
    // Fetch detail to get timeout_s/max_tokens/temperature not in list
    try {
      const res = await adminApi.getLlmConfigDetail(row.id)
      const d = res.data
      form.timeout_s = d.timeout_s ?? 60
      form.max_tokens = d.max_tokens ?? 8000
      form.temperature = d.temperature ?? 0.7
    } catch {
      form.timeout_s = 60
      form.max_tokens = 8000
      form.temperature = 0.7
    }
  } else {
    editingId.value = null
    resetForm()
  }
  dialogVisible.value = true
}

function resetForm() {
  form.name = ''
  form.provider = 'openai-compatible'
  form.base_url = ''
  form.model_name = ''
  form.api_key = ''
  form.timeout_s = 60
  form.max_tokens = 8000
  form.temperature = 0.7
  form.is_default = false
  formRef.value?.resetFields()
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = { ...form }
    if (dialogMode.value === 'edit') {
      delete payload.provider
      if (!payload.api_key) delete payload.api_key
    }
    if (dialogMode.value === 'add') {
      await adminApi.createLlmConfig(payload)
      ElMessage.success('创建成功')
    } else {
      await adminApi.updateLlmConfig(editingId.value, payload)
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    fetchConfigs()
  } catch { /* ignore */ }
  finally { submitting.value = false }
}

function handleTest(row) {
  testingId.value = row.id
  testPrompt.value = '请回复 OK'
  testResult.value = null
  testVisible.value = true
}

async function doTest() {
  testing.value = true
  testResult.value = null
  try {
    const res = await adminApi.testLlmConfig(testingId.value, testPrompt.value)
    testResult.value = res.data
    if (res.data?.status === 'success') {
      ElMessage.success(res.data.message || '连接测试成功')
    } else {
      ElMessage.error(res.data?.message || '连接测试失败')
    }
    fetchConfigs()
  } catch (error) {
    const message = error.response?.data?.message || error.message || '连接测试失败'
    testResult.value = {
      status: 'failed',
      message,
    }
  }
  finally { testing.value = false }
}

async function handleEnable(row) {
  try {
    await adminApi.enableLlmConfig(row.id)
    ElMessage.success('已启用')
    fetchConfigs()
  } catch { /* ignore */ }
}

async function handleDisable(row) {
  try {
    await adminApi.disableLlmConfig(row.id)
    ElMessage.success('已停用')
    fetchConfigs()
  } catch { /* ignore */ }
}

onMounted(() => fetchConfigs())
</script>

<style lang="scss" scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  h3 { font-size: 18px; }
}

.test-result {
  margin-top: 16px;
  padding: 16px;
  border-radius: 6px;

  &.success { background: #f0f9eb; }
  &.failed { background: #fef0f0; }

  p { margin-bottom: 4px; font-size: 13px; }
}
</style>
