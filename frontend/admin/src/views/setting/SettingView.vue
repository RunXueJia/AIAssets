<template>
  <div class="setting-page">
    <page-header title="系统设置" />

    <el-card v-loading="loading" class="setting-card">
      <template v-if="settingsLoaded">
        <el-form :model="form" label-width="160px">
          <h3 class="section-title">默认设置</h3>
          <el-form-item label="默认生成数量">
            <el-input-number v-model="form.default_count" :min="1" :max="20" />
          </el-form-item>
          <el-form-item label="默认抓取数量">
            <el-input-number v-model="form.default_fetch_limit" :min="5" :max="100" />
          </el-form-item>

          <h3 class="section-title">栏目开关</h3>
          <el-form-item v-for="col in form.enabled_columns" :key="col.value" :label="col.label">
            <el-switch v-model="col.enabled" />
          </el-form-item>

          <h3 class="section-title">模型配置</h3>
          <el-form-item label="模型供应商">
            <el-select v-model="form.model_provider" style="width: 280px">
              <el-option label="OpenAI 兼容接口" value="openai_compatible" />
              <el-option label="OpenAI" value="openai" />
            </el-select>
          </el-form-item>
          <el-form-item label="接口地址">
            <el-input v-model="form.model_base_url" placeholder="https://api.example.com/v1" style="width: 400px" />
          </el-form-item>
          <el-form-item label="API 密钥">
            <el-input v-model="form.model_api_key" type="password" show-password placeholder="sk-xxx" style="width: 400px" />
            <div v-if="originalSettings.model_key_masked && !form.model_api_key" class="form-hint">
              当前密钥: {{ originalSettings.model_key_masked }}
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="saving" @click="saveSettings">保存设置</el-button>
          </el-form-item>
        </el-form>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSetting, updateSetting } from '@/api/setting'
import PageHeader from '@/components/common/PageHeader.vue'

const loading = ref(false)
const saving = ref(false)
const settingsLoaded = ref(false)
const originalSettings = reactive({})

const form = reactive({
  default_count: 5,
  default_fetch_limit: 20,
  enabled_columns: [],
  model_provider: 'openai_compatible',
  model_base_url: '',
  model_api_key: '',
})

async function fetchSettings() {
  loading.value = true
  try {
    const data = await getSetting()
    Object.assign(originalSettings, data)
    form.default_count = data.default_count || 5
    form.default_fetch_limit = data.default_fetch_limit || 20
    form.enabled_columns = (data.enabled_columns || []).map((c) => ({ ...c }))
    form.model_provider = data.model_provider || 'openai_compatible'
    form.model_base_url = data.model_base_url || ''
    form.model_api_key = ''
    settingsLoaded.value = true
  } catch {}
  loading.value = false
}

async function saveSettings() {
  saving.value = true
  try {
    await updateSetting({
      default_count: form.default_count,
      default_fetch_limit: form.default_fetch_limit,
      enabled_columns: form.enabled_columns.filter((c) => c.enabled).map((c) => c.value),
      model_provider: form.model_provider,
      model_base_url: form.model_base_url || undefined,
      model_api_key: form.model_api_key || undefined,
    })
    ElMessage.success('设置已保存')
  } catch {}
  saving.value = false
}

onMounted(() => fetchSettings())
</script>

<style scoped lang="scss">
.setting-card {
  max-width: 700px;
}

.section-title {
  font-size: 15px;
  color: #303133;
  margin: 24px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
