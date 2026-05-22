<template>
  <div class="llm-config-page page-shell">
    <div class="page-heading">
      <div>
        <h2>LLM 配置管理</h2>
        <p>维护模型供应商、接口格式、密钥状态和在线调试结果。</p>
      </div>
      <el-button type="primary" @click="openDialog('add')">添加配置</el-button>
    </div>

    <div class="table-panel">
      <el-table :data="configs" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="provider" label="供应商" width="150" show-overflow-tooltip />
        <el-table-column label="API 格式" width="190" show-overflow-tooltip>
          <template #default="{ row }">{{ apiFormatLabel(row.api_format) }}</template>
        </el-table-column>
        <el-table-column label="API 地址" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">{{ row.base_url }}</template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型" min-width="150" show-overflow-tooltip />
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
            <span v-else class="muted-text">-</span>
          </template>
        </el-table-column>
        <el-table-column label="测试状态" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.last_test_status === 'success'" type="success" size="small">通过</el-tag>
            <el-tag v-else-if="row.last_test_status === 'failed'" type="danger" size="small">失败</el-tag>
            <span v-else class="muted-text">未测试</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
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
        <template #empty>
          <el-empty description="暂无 LLM 配置" />
        </template>
      </el-table>
    </div>

    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :total="total"
        :page-size="pageSize"
        layout="total, prev, pager, next"
        @current-change="fetchConfigs"
      />
    </div>

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
        <el-form-item label="API 格式" prop="api_format" :rules="[{ required: true, message: '请选择 API 格式' }]">
          <el-select v-model="form.api_format" placeholder="选择 API 格式" style="width: 100%">
            <el-option
              v-for="item in apiFormatOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
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
    <el-dialog
      v-model="testVisible"
      class="llm-chat-dialog"
      width="390px"
      :show-close="false"
      :close-on-click-modal="!testing"
      @closed="handleTestDialogClosed"
    >
      <div class="llm-chat-shell">
        <header class="chat-topbar">
          <button type="button" class="topbar-text-btn" :disabled="testing" @click="resetTestChat">
            新对话
          </button>
          <div class="chat-title">
            <span>{{ currentTestConfig?.name || 'LLM 调试' }}</span>
            <small>{{ currentTestConfig?.model_name || '模型对话测试' }}</small>
          </div>
          <button type="button" class="topbar-icon-btn" @click="testVisible = false">
            <el-icon><Close /></el-icon>
          </button>
        </header>

        <div class="chat-hint">内容由模型生成，请仔细甄别</div>

        <main ref="testChatBodyRef" class="chat-debug">
          <div v-if="!testMessages.length" class="chat-empty">
            <div class="empty-mark">
              <el-icon><ChatRound /></el-icon>
            </div>
            <p>发送一条消息，测试当前 LLM 配置的流式响应。</p>
          </div>

          <div
            v-for="message in testMessages"
            :key="message.id"
            class="chat-message"
            :class="message.role"
          >
            <div v-if="message.role === 'assistant'" class="assistant-mark">AI</div>
            <div class="chat-bubble">
              <span v-if="message.content">{{ message.content }}</span>
              <span v-else class="typing-dots">
                <i></i>
                <i></i>
                <i></i>
              </span>
            </div>
          </div>
        </main>

        <div v-if="testResult" class="test-result" :class="testResult.status">
          <span>{{ testResult.status === 'success' ? '连接测试成功' : '连接测试失败' }}</span>
          <span v-if="testResult.duration_ms">{{ (testResult.duration_ms / 1000).toFixed(1) }}s</span>
        </div>

        <form class="chat-composer" @submit.prevent="doTestStream">
          <el-input
            v-model="testPrompt"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="发消息..."
            :disabled="testing"
            @keydown.enter.exact.prevent="doTestStream"
          />
          <div class="composer-toolbar">
            <div class="composer-tools-left">

            </div>
            <button
              v-if="testing"
              type="button"
              class="send-btn stop"
              aria-label="停止响应"
              @click="abortTestStream"
            >
              <el-icon><VideoPause /></el-icon>
            </button>
            <button
              v-else
              type="submit"
              class="send-btn"
              :disabled="!testPrompt.trim()"
              aria-label="发送消息"
            >
              <el-icon><Position /></el-icon>
            </button>
          </div>
        </form>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import { useLoading } from '@/composables/useLoading'
import { useAuthStore } from '@/stores/auth'
import {
  ChatRound,
  Close,
  Grid,
  Lightning,
  Plus,
  Position,
  VideoPause,
} from '@element-plus/icons-vue'

const { loading, withLoading } = useLoading()
const auth = useAuthStore()
const configs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const apiFormatOptions = [
  { label: 'OpenAI Chat Completions', value: 'openai_chat_completions' },
  { label: 'OpenAI Responses API', value: 'openai_responses' },
  { label: 'Anthropic Messages', value: 'anthropic_messages' },
  { label: 'Gemini Native generateContent', value: 'gemini_generate_content' },
]

const dialogVisible = ref(false)
const dialogMode = ref('add')
const submitting = ref(false)
const formRef = ref(null)
const editingId = ref(null)

const form = reactive({
  name: '',
  provider: 'openai-compatible',
  api_format: 'openai_chat_completions',
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
const testMessages = ref([])
const testingId = ref(null)
const testAbortController = ref(null)
const currentTestConfig = ref(null)
const testChatBodyRef = ref(null)

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
    form.api_format = row.api_format || 'openai_chat_completions'
    form.base_url = row.base_url
    form.model_name = row.model_name
    form.api_key = ''
    form.is_default = row.is_default
    // Fetch detail to get timeout_s/max_tokens/temperature not in list
    try {
      const res = await adminApi.getLlmConfigDetail(row.id)
      const d = res.data
      form.api_format = d.api_format || 'openai_chat_completions'
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
  form.api_format = 'openai_chat_completions'
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
  currentTestConfig.value = row
  testPrompt.value = '你好'
  testResult.value = null
  testMessages.value = []
  testVisible.value = true
}

async function doTestStream() {
  const prompt = testPrompt.value.trim()
  if (!prompt || testing.value) return

  testing.value = true
  testResult.value = null
  abortTestStream()
  const messageSeed = Date.now()
  testMessages.value.push(
    { id: `user-${messageSeed}`, role: 'user', content: prompt },
    { id: `assistant-${messageSeed}`, role: 'assistant', content: '' },
  )
  testPrompt.value = ''
  scrollTestChatToBottom()

  const controller = new AbortController()
  testAbortController.value = controller
  try {
    const response = await adminApi.testLlmConfigStream(
      testingId.value,
      prompt,
      auth.token,
      controller.signal,
    )
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.message || `HTTP ${response.status}`)
    }
    await readTestStream(response)
    fetchConfigs()
  } catch (error) {
    if (error.name === 'AbortError') return
    const message = error.response?.data?.message || error.message || '连接测试失败'
    testResult.value = {
      status: 'failed',
      message,
    }
    updateAssistantMessage(message)
  }
  finally { testing.value = false }
}

async function readTestStream(response) {
  if (!response.body) throw new Error('流式响应为空')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let eventType = ''
  let eventDataLines = []

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        eventDataLines.push(line.slice(6))
      } else if (line === '' && eventType && eventDataLines.length) {
        handleTestEvent(eventType, eventDataLines.join('\n'))
        eventType = ''
        eventDataLines = []
      }
    }
  }

  if (eventType && eventDataLines.length) {
    handleTestEvent(eventType, eventDataLines.join('\n'))
  }
}

function handleTestEvent(type, data) {
  const payload = JSON.parse(data)
  if (type === 'token') {
    updateAssistantMessage(payload.content || '')
    return
  }
  if (type === 'done') {
    testResult.value = payload
    return
  }
  if (type === 'error') {
    testResult.value = payload
    updateAssistantMessage(payload.message || '')
    ElMessage.error(payload.message || '连接测试失败')
  }
}

function updateAssistantMessage(content) {
  const assistantMessages = testMessages.value.filter((item) => item.role === 'assistant')
  const message = assistantMessages[assistantMessages.length - 1]
  if (message) {
    message.content += content
    scrollTestChatToBottom()
  }
}

function abortTestStream() {
  if (testAbortController.value) {
    testAbortController.value.abort()
    testAbortController.value = null
  }
}

function resetTestChat() {
  abortTestStream()
  testing.value = false
  testPrompt.value = '你好'
  testResult.value = null
  testMessages.value = []
}

function handleTestDialogClosed() {
  abortTestStream()
  testing.value = false
}

function scrollTestChatToBottom() {
  nextTick(() => {
    if (testChatBodyRef.value) {
      testChatBodyRef.value.scrollTop = testChatBodyRef.value.scrollHeight
    }
  })
}

function apiFormatLabel(value) {
  return apiFormatOptions.find((item) => item.value === value)?.label || value || '-'
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
.llm-config-page {
  max-width: 1380px;
}

.muted-text {
  color: $text-muted;
}

:deep(.llm-chat-dialog) {
  --el-dialog-padding-primary: 0;
  overflow: hidden;
  background: #fff;
  border-radius: 14px;

  .el-dialog__header,
  .el-dialog__body {
    padding: 0;
  }
}

.llm-chat-shell {
  display: flex;
  flex-direction: column;
  height: min(720px, calc(100vh - 56px));
  min-height: 560px;
  background: #fff;
}

.chat-topbar {
  display: grid;
  grid-template-columns: 82px 1fr 38px;
  align-items: center;
  gap: 8px;
  height: 48px;
  padding: 0 12px 0 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.topbar-text-btn,
.topbar-icon-btn,
.tool-icon,
.quick-chip,
.send-btn {
  border: 0;
  cursor: pointer;
  transition:
    color 0.16s ease,
    background 0.16s ease,
    border-color 0.16s ease,
    transform 0.16s ease;

  &:disabled {
    cursor: not-allowed;
    opacity: 0.45;
  }
}

.topbar-text-btn {
  justify-self: start;
  color: $text-primary;
  font-size: 14px;
  font-weight: 600;
  background: transparent;

  &:not(:disabled):hover {
    color: $color-primary;
  }
}

.topbar-icon-btn {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  color: $text-secondary;
  background: transparent;
  border-radius: 999px;

  &:hover {
    color: $text-primary;
    background: $surface-muted;
  }
}

.chat-title {
  min-width: 0;
  text-align: center;

  span,
  small {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  span {
    color: $text-primary;
    font-size: 14px;
    font-weight: 700;
  }

  small {
    margin-top: 2px;
    color: $text-muted;
    font-size: 11px;
    font-weight: 500;
  }
}

.chat-hint {
  height: 24px;
  padding-left: 16px;
  color: #c3cad5;
  font-size: 11px;
  line-height: 24px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.04);
}

.test-result {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 30px;
  margin: 0 16px 8px;
  padding: 6px 12px;
  border: 1px solid $border-light;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;

  &.success {
    border-color: rgba(22, 163, 74, 0.18);
    background: rgba(22, 163, 74, 0.08);
  }

  &.failed {
    border-color: rgba(220, 38, 38, 0.18);
    background: rgba(220, 38, 38, 0.08);
  }
}

.chat-debug {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 18px;
  padding: 28px 16px 20px;
  overflow-y: auto;
  background: #fff;
}

.chat-empty {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 260px;
  color: $text-muted;
  text-align: center;

  p {
    max-width: 220px;
    color: $text-muted;
    font-size: 13px;
    line-height: 1.6;
  }
}

.empty-mark {
  display: grid;
  width: 54px;
  height: 54px;
  place-items: center;
  color: $color-primary;
  background: $surface-strong;
  border-radius: 18px;

  .el-icon {
    font-size: 26px;
  }
}

.chat-message {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  max-width: 90%;

  &.user {
    align-self: flex-end;
    justify-content: flex-end;

    .chat-bubble {
      color: $text-primary;
      background: #f4f5f7;
      border-radius: 16px 16px 4px 16px;
    }
  }

  &.assistant {
    align-self: flex-start;

    .chat-bubble {
      color: $text-primary;
      background: transparent;
      border-radius: 0;
    }
  }
}

.assistant-mark {
  display: grid;
  margin-top: 8px;
  width: 26px;
  height: 26px;
  flex: 0 0 auto;
  place-items: center;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  background: $text-primary;
  border-radius: 50%;
}

.chat-bubble {
  min-height: 40px;
  max-width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.typing-dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 42px;
  min-height: 20px;

  i {
    width: 5px;
    height: 5px;
    background: $text-muted;
    border-radius: 50%;
    animation: chat-dot 1s infinite ease-in-out;

    &:nth-child(2) {
      animation-delay: 0.16s;
    }

    &:nth-child(3) {
      animation-delay: 0.32s;
    }
  }
}

@keyframes chat-dot {
  0%,
  80%,
  100% {
    opacity: 0.35;
    transform: translateY(0);
  }

  40% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

.chat-composer {
  margin: 0 16px 16px;
  padding: 12px 14px 10px;
  background: #fff;
  border: 1px solid rgba(37, 99, 235, 0.28);
  border-radius: 22px;
  box-shadow:
    0 10px 32px rgba(37, 99, 235, 0.14),
    0 1px 0 rgba(255, 255, 255, 0.9) inset;

  :deep(.el-textarea__inner) {
    min-height: 42px !important;
    padding: 2px 0 8px;
    color: $text-primary;
    background: transparent;
    border: 0;
    border-radius: 0;
    box-shadow: none !important;
    resize: none;

    &::placeholder {
      color: #a6afbd;
    }
  }
}

.composer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.composer-tools-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tool-icon {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  color: $text-primary;
  background: transparent;
  border-radius: 999px;

  &:not(:disabled):hover {
    background: $surface-muted;
  }
}

.quick-chip,
.more-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 28px;
  color: $text-primary;
  font-size: 12px;
  font-weight: 650;
  background: transparent;
}

.quick-chip {
  padding: 0;

  &:not(:disabled):hover {
    color: $color-primary;
  }

  .el-icon {
    color: $color-primary;
  }
}

.more-chip .el-icon {
  color: $text-primary;
}

.send-btn {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  color: #fff;
  background: $text-primary;
  border-radius: 50%;

  &:not(:disabled):hover {
    transform: translateY(-1px);
  }

  &.stop {
    background: $color-danger;
  }
}

@media (max-width: 720px) {
  :deep(.llm-chat-dialog) {
    width: calc(100vw - 20px) !important;
  }

  .llm-chat-shell {
    height: calc(100vh - 32px);
    min-height: 520px;
  }
}
</style>
