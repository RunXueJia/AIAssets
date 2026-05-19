<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">
          LLM 中心
        </h1>
        <p class="page-subtitle">
          管理供应商、模型、Prompt 模板、调试流和调用成本。
        </p>
      </div>
      <el-tag
        type="info"
        effect="plain"
      >
        API Key 仅展示脱敏值
      </el-tag>
    </div>

    <div class="metric-grid">
      <div class="metric-card surface">
        <div class="metric-label">
          总调用
        </div>
        <div class="metric-value">
          {{ cost.total_calls || 0 }}
        </div>
      </div>
      <div class="metric-card surface">
        <div class="metric-label">
          费用估算
        </div>
        <div class="metric-value">
          {{ cost.total_cost || 0 }}
        </div>
      </div>
      <div class="metric-card surface">
        <div class="metric-label">
          平均首 token
        </div>
        <div class="metric-value">
          {{ cost.avg_first_token_ms || 0 }}ms
        </div>
      </div>
      <div class="metric-card surface">
        <div class="metric-label">
          流式协议
        </div>
        <div class="metric-value">
          SSE
        </div>
      </div>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane
        label="供应商"
        name="providers"
      >
        <DataPanel
          :items="providers.items"
          :total="providers.total"
          :loading="loading"
          @search="handleSearch"
        >
          <template #actions>
            <PermissionGate permission="llm:provider:create">
              <el-button
                type="primary"
                @click="openProviderForm()"
              >
                新增供应商
              </el-button>
            </PermissionGate>
          </template>
          <el-table-column
            prop="name"
            label="名称"
            min-width="180"
          />
          <el-table-column
            prop="provider_type"
            label="类型"
            width="170"
          />
          <el-table-column
            prop="base_url"
            label="Base URL"
            min-width="260"
          />
          <el-table-column
            prop="api_key"
            label="API Key"
            width="140"
          />
          <el-table-column
            label="状态"
            width="100"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="120"
          >
            <template #default="{ row }">
              <el-button
                text
                type="primary"
                @click="openProviderForm(row)"
              >
                编辑
              </el-button>
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>

      <el-tab-pane
        label="模型"
        name="models"
      >
        <DataPanel
          :items="models.items"
          :total="models.total"
          :loading="loading"
          @search="handleSearch"
        >
          <template #actions>
            <PermissionGate permission="llm:model:create">
              <el-button
                type="primary"
                @click="openModelForm()"
              >
                新增模型
              </el-button>
            </PermissionGate>
          </template>
          <el-table-column
            prop="display_name"
            label="展示名"
            min-width="180"
          />
          <el-table-column
            prop="model_name"
            label="模型名"
            min-width="180"
          />
          <el-table-column
            prop="usage_type"
            label="用途"
            min-width="160"
          />
          <el-table-column
            prop="context_window"
            label="上下文"
            width="110"
          />
          <el-table-column
            prop="temperature"
            label="温度"
            width="90"
          />
          <el-table-column
            label="状态"
            width="100"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="120"
          >
            <template #default="{ row }">
              <el-button
                text
                type="primary"
                @click="openModelForm(row)"
              >
                编辑
              </el-button>
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>

      <el-tab-pane
        label="Prompt 模板"
        name="prompts"
      >
        <DataPanel
          :items="prompts.items"
          :total="prompts.total"
          :loading="loading"
          @search="handleSearch"
        >
          <template #actions>
            <PermissionGate permission="llm:prompt:create">
              <el-button
                type="primary"
                @click="openPromptForm()"
              >
                新增模板
              </el-button>
            </PermissionGate>
            <PermissionGate permission="llm:prompt:test">
              <el-button
                @click="debugVisible = true"
              >
                调试模板
              </el-button>
            </PermissionGate>
          </template>
          <el-table-column
            prop="name"
            label="模板"
            min-width="180"
          />
          <el-table-column
            prop="scene"
            label="场景"
            width="170"
          />
          <el-table-column
            prop="version"
            label="版本"
            width="90"
          />
          <el-table-column
            label="变量"
            min-width="220"
          >
            <template #default="{ row }">
              {{ row.variables?.join(', ') }}
            </template>
          </el-table-column>
          <el-table-column
            label="状态"
            width="100"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="120"
          >
            <template #default="{ row }">
              <el-button
                text
                type="primary"
                @click="openPromptForm(row)"
              >
                编辑
              </el-button>
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>

      <el-tab-pane
        label="调用日志"
        name="logs"
      >
        <DataPanel
          :items="logs.items"
          :total="logs.total"
          :loading="loading"
          @search="handleSearch"
        >
          <el-table-column
            prop="scene"
            label="场景"
            min-width="160"
          />
          <el-table-column
            prop="model_id"
            label="模型"
            width="120"
          />
          <el-table-column
            prop="first_token_ms"
            label="首 token"
            width="100"
          />
          <el-table-column
            prop="duration_ms"
            label="耗时"
            width="100"
          />
          <el-table-column
            prop="estimated_cost"
            label="成本"
            width="90"
          />
          <el-table-column
            label="状态"
            width="110"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>
    </el-tabs>

    <el-drawer
      v-model="debugVisible"
      title="Prompt 调试"
      size="720"
    >
      <el-form
        label-position="top"
        :model="debugForm"
      >
        <el-form-item label="模板 ID">
          <el-input v-model="debugForm.prompt_template_id" />
        </el-form-item>
        <el-form-item label="模型 ID">
          <el-input v-model="debugForm.model_id" />
        </el-form-item>
        <el-form-item label="变量 JSON">
          <el-input
            v-model="debugForm.variables"
            type="textarea"
            :rows="6"
            class="mono"
          />
        </el-form-item>
      </el-form>
      <SseOutputPanel
        title="Prompt 调试流"
        :text="stream.text"
        :raw="stream.raw"
        :stats="stream.stats"
        :streaming="stream.streaming"
        :interrupted="stream.interrupted"
        @start="startDebug"
        @stop="stopDebug"
      />
    </el-drawer>

    <el-drawer
      v-model="providerDrawerVisible"
      :title="providerForm.id ? '编辑供应商' : '新增供应商'"
      size="560"
    >
      <el-form
        label-position="top"
        :model="providerForm"
      >
        <el-form-item label="供应商名称">
          <el-input v-model="providerForm.name" />
        </el-form-item>
        <el-form-item label="供应商类型">
          <el-select
            v-model="providerForm.provider_type"
            style="width: 100%"
          >
            <el-option
              label="OpenAI Compatible"
              value="openai_compatible"
            />
            <el-option
              label="Local Model"
              value="local_model"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input
            v-model="providerForm.base_url"
            placeholder="https://api.example.com/v1"
          />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="providerForm.api_key"
            type="password"
            show-password
            placeholder="保存后列表仅展示脱敏值"
          />
        </el-form-item>
        <el-form-item label="超时时间（秒）">
          <el-input-number
            v-model="providerForm.timeout_seconds"
            :min="5"
            :max="300"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="providerForm.status"
            active-value="enabled"
            inactive-value="disabled"
          />
        </el-form-item>
        <el-button
          type="primary"
          :loading="submitting"
          @click="saveProvider"
        >
          保存供应商
        </el-button>
      </el-form>
    </el-drawer>

    <el-drawer
      v-model="modelDrawerVisible"
      :title="modelForm.id ? '编辑模型' : '新增模型'"
      size="640"
    >
      <el-form
        label-position="top"
        :model="modelForm"
      >
        <el-form-item label="所属供应商">
          <el-select
            v-model="modelForm.provider_id"
            style="width: 100%"
          >
            <el-option
              v-for="provider in providers.items"
              :key="provider.id"
              :label="provider.name"
              :value="provider.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="后台展示名">
          <el-input v-model="modelForm.display_name" />
        </el-form-item>
        <el-form-item label="实际模型名">
          <el-input
            v-model="modelForm.model_name"
            placeholder="gpt-4.1-mini"
          />
        </el-form-item>
        <el-form-item label="用途">
          <el-select
            v-model="modelForm.usage_type"
            style="width: 100%"
          >
            <el-option
              v-for="usage in modelUsageOptions"
              :key="usage.value"
              :label="usage.label"
              :value="usage.value"
            />
          </el-select>
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="上下文长度">
            <el-input-number
              v-model="modelForm.context_window"
              :min="1024"
              :step="1024"
            />
          </el-form-item>
          <el-form-item label="最大输出 token">
            <el-input-number
              v-model="modelForm.max_output_tokens"
              :min="256"
              :step="256"
            />
          </el-form-item>
          <el-form-item label="默认温度">
            <el-input-number
              v-model="modelForm.temperature"
              :min="0"
              :max="2"
              :step="0.1"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-switch
              v-model="modelForm.status"
              active-value="enabled"
              inactive-value="disabled"
            />
          </el-form-item>
          <el-form-item label="输入 token 单价">
            <el-input-number
              v-model="modelForm.input_token_price"
              :min="0"
              :precision="6"
              :step="0.000001"
            />
          </el-form-item>
          <el-form-item label="输出 token 单价">
            <el-input-number
              v-model="modelForm.output_token_price"
              :min="0"
              :precision="6"
              :step="0.000001"
            />
          </el-form-item>
        </div>
        <el-button
          type="primary"
          :loading="submitting"
          @click="saveModel"
        >
          保存模型
        </el-button>
      </el-form>
    </el-drawer>

    <el-drawer
      v-model="promptDrawerVisible"
      :title="promptForm.id ? '编辑 Prompt 模板' : '新增 Prompt 模板'"
      size="760"
    >
      <el-form
        label-position="top"
        :model="promptForm"
      >
        <div class="form-grid">
          <el-form-item label="模板名称">
            <el-input v-model="promptForm.name" />
          </el-form-item>
          <el-form-item label="场景">
            <el-input
              v-model="promptForm.scene"
              placeholder="topic_generation"
            />
          </el-form-item>
          <el-form-item label="版本">
            <el-input-number
              v-model="promptForm.version"
              :min="1"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-switch
              v-model="promptForm.status"
              active-value="enabled"
              inactive-value="disabled"
            />
          </el-form-item>
        </div>
        <el-form-item label="变量，逗号分隔">
          <el-input v-model="promptVariablesText" />
        </el-form-item>
        <el-form-item label="System Prompt">
          <el-input
            v-model="promptForm.system_prompt"
            type="textarea"
            :rows="4"
          />
        </el-form-item>
        <el-form-item label="User Prompt">
          <el-input
            v-model="promptForm.user_prompt"
            type="textarea"
            :rows="5"
          />
        </el-form-item>
        <el-form-item label="JSON Schema">
          <el-input
            v-model="promptSchemaText"
            type="textarea"
            :rows="8"
            class="mono"
          />
        </el-form-item>
        <el-button
          type="primary"
          :loading="submitting"
          @click="savePrompt"
        >
          保存模板
        </el-button>
      </el-form>
    </el-drawer>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref, watch } from 'vue'
import { llmApi } from '@/api'
import DataPanel from '@/components/DataPanel.vue'
import PermissionGate from '@/components/PermissionGate.vue'
import SseOutputPanel from '@/components/SseOutputPanel.vue'
import StatusTag from '@/components/StatusTag.vue'
import { streamOpenAiSse } from '@/utils/sseClient'

const tab = ref('providers')
const loading = ref(false)
const query = reactive({ page: 1, page_size: 20, keyword: '' })
const cost = ref({})
const providers = reactive({ items: [], total: 0 })
const models = reactive({ items: [], total: 0 })
const prompts = reactive({ items: [], total: 0 })
const logs = reactive({ items: [], total: 0 })
const debugVisible = ref(false)
const providerDrawerVisible = ref(false)
const modelDrawerVisible = ref(false)
const promptDrawerVisible = ref(false)
const submitting = ref(false)
const providerForm = reactive(createProviderForm())
const modelForm = reactive(createModelForm())
const promptForm = reactive(createPromptForm())
const promptVariablesText = ref('')
const promptSchemaText = ref('')
const streamController = ref(null)
const debugForm = reactive({
  prompt_template_id: 'prompt_1',
  model_id: 'model_1',
  variables: '{\n  "column_name": "一分钟 AI 办公",\n  "count": 5\n}'
})
const stream = reactive({
  text: '',
  raw: '',
  streaming: false,
  interrupted: false,
  stats: { chunkCount: 0, firstTokenMs: 0 }
})

const modelUsageOptions = [
  { label: '选题生成', value: 'topic' },
  { label: '脚本生成', value: 'script' },
  { label: '分镜生成', value: 'storyboard' },
  { label: '质量检查', value: 'quality_check' },
  { label: '图文页', value: 'article' },
  { label: '知识卡片', value: 'card' },
  { label: '资料包', value: 'download_asset' },
  { label: '日报建议', value: 'report' },
  { label: '内容生成', value: 'content_generation' }
]

async function load() {
  loading.value = true
  try {
    const params = { ...query }
    const loaders = {
      providers: () => llmApi.getProviders(params).then(assignList(providers)),
      models: () => llmApi.getModels(params).then(assignList(models)),
      prompts: () => llmApi.getPrompts(params).then(assignList(prompts)),
      logs: () => llmApi.getLogs(params).then(assignList(logs))
    }
    await loaders[tab.value]()
    cost.value = await llmApi.getCostSummary()
  } finally {
    loading.value = false
  }
}

function assignList(target) {
  return (data) => {
    target.items = data.items
    target.total = data.total
  }
}

function handleSearch(keyword) {
  query.keyword = keyword
  query.page = 1
  load()
}

function createProviderForm() {
  return {
    id: '',
    name: '',
    provider_type: 'openai_compatible',
    base_url: '',
    api_key: '',
    timeout_seconds: 60,
    status: 'enabled'
  }
}

function createModelForm() {
  return {
    id: '',
    provider_id: '',
    model_name: '',
    display_name: '',
    usage_type: 'topic',
    context_window: 128000,
    max_output_tokens: 4096,
    temperature: 0.7,
    input_token_price: 0,
    output_token_price: 0,
    status: 'enabled'
  }
}

function createPromptForm() {
  return {
    id: '',
    scene: 'topic_generation',
    version: 1,
    name: '',
    system_prompt: '',
    user_prompt: '',
    variables: [],
    output_schema: {
      type: 'object',
      properties: {},
      required: []
    },
    status: 'enabled'
  }
}

function resetReactive(target, source) {
  Object.keys(target).forEach((key) => {
    delete target[key]
  })
  Object.assign(target, source)
}

function openProviderForm(row = null) {
  resetReactive(providerForm, row ? { ...createProviderForm(), ...row } : createProviderForm())
  providerDrawerVisible.value = true
}

async function openModelForm(row = null) {
  if (!providers.items.length) {
    const providerData = await llmApi.getProviders()
    providers.items = providerData.items || []
    providers.total = providerData.total || providers.items.length
  }
  const nextForm = row ? { ...createModelForm(), ...row } : createModelForm()
  nextForm.provider_id = nextForm.provider_id || providers.items[0]?.id || ''
  resetReactive(modelForm, nextForm)
  modelDrawerVisible.value = true
}

function openPromptForm(row = null) {
  const nextForm = row ? { ...createPromptForm(), ...row } : createPromptForm()
  resetReactive(promptForm, nextForm)
  promptVariablesText.value = Array.isArray(nextForm.variables) ? nextForm.variables.join(', ') : ''
  promptSchemaText.value = JSON.stringify(nextForm.output_schema || createPromptForm().output_schema, null, 2)
  promptDrawerVisible.value = true
}

async function saveProvider() {
  submitting.value = true
  try {
    await llmApi.saveProvider({ ...providerForm })
    ElMessage.success('供应商已保存')
    providerDrawerVisible.value = false
    tab.value = 'providers'
    await load()
  } finally {
    submitting.value = false
  }
}

async function saveModel() {
  submitting.value = true
  try {
    await llmApi.saveModel({ ...modelForm })
    ElMessage.success('模型已保存')
    modelDrawerVisible.value = false
    tab.value = 'models'
    await load()
  } finally {
    submitting.value = false
  }
}

async function savePrompt() {
  let outputSchema
  try {
    outputSchema = JSON.parse(promptSchemaText.value || '{}')
  } catch {
    ElMessage.error('JSON Schema 格式不正确')
    return
  }

  submitting.value = true
  try {
    await llmApi.savePrompt({
      ...promptForm,
      variables: promptVariablesText.value
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
      output_schema: outputSchema
    })
    ElMessage.success('Prompt 模板已保存')
    promptDrawerVisible.value = false
    tab.value = 'prompts'
    await load()
  } finally {
    submitting.value = false
  }
}

async function startDebug() {
  stream.text = ''
  stream.raw = ''
  stream.streaming = true
  stream.interrupted = false
  stream.stats = { chunkCount: 0, firstTokenMs: 0 }
  streamController.value = new AbortController()
  let variables = {}
  try {
    variables = JSON.parse(debugForm.variables || '{}')
  } catch {
    ElMessage.error('变量 JSON 格式不正确')
    stream.streaming = false
    return
  }

  try {
    await streamOpenAiSse(
      '/prompt_templates/stream_test_prompt_template',
      {
        prompt_template_id: debugForm.prompt_template_id,
        model_id: debugForm.model_id,
        variables
      },
      {
        onFirstToken: ({ firstTokenMs }) => {
          stream.stats.firstTokenMs = Math.round(firstTokenMs)
        },
        onChunk: (chunk) => {
          stream.raw += `data: ${JSON.stringify(chunk)}\n\n`
          stream.stats.chunkCount += 1
        },
        onDelta: (_delta, context) => {
          stream.text = context.text
        },
        onDone: () => {
          stream.streaming = false
        },
        onInterrupted: () => {
          stream.interrupted = true
        }
      },
      { controller: streamController.value }
    )
  } catch (error) {
    stream.interrupted = true
    ElMessage.error(error.message || 'Prompt 调试失败')
  } finally {
    stream.streaming = false
    streamController.value = null
  }
}

function stopDebug() {
  streamController.value?.abort()
  stream.streaming = false
  stream.interrupted = true
}

watch(tab, load)
onMounted(load)
</script>

<style scoped lang="scss">
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}
</style>
