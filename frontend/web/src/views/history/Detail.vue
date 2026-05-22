<template>
  <div class="detail-page" v-loading="loading">
    <template v-if="detail">
      <button class="back-link" @click="$router.push('/history')">
        <el-icon><ArrowLeft /></el-icon> 返回
      </button>

      <div class="detail-header">
        <div>
          <h2>{{ detail.input?.origin_text || '' }} → {{ detail.input?.destination_text || '' }}</h2>
          <div class="detail-tags">
            <span class="status-badge" :class="recordStatus">{{ statusLabel(recordStatus) }}</span>
            <span class="info-tag">{{ transportLabel(detail.record?.transport_mode) }}</span>
            <span class="info-tag" v-if="detail.record?.duration_ms">{{ (detail.record.duration_ms / 1000).toFixed(1) }}s</span>
            <span class="info-tag">{{ detail.record?.created_at }}</span>
          </div>
        </div>
        <button
          v-if="recordStatus === 'failed'"
          type="button"
          class="retry-btn"
          :disabled="streaming"
          @click="handleRetry"
        >
          <el-icon><Refresh /></el-icon> 重试
        </button>
      </div>

      <div v-if="streaming || streamTokens || streamErrorMessage" class="section-card process-card">
        <div class="process-head">
          <h4><el-icon><Loading /></el-icon>生成过程</h4>
          <span v-if="currentStageName" class="stage-pill">{{ currentStageName }}</span>
          <button v-if="streaming" type="button" class="stop-btn" @click="stopStream">停止</button>
        </div>
        <p v-if="streamErrorMessage" class="error-text">{{ streamErrorMessage }}</p>
        <div v-if="streamTokens" class="stream-tokens" v-html="renderedTokens"></div>
        <span v-if="streaming" class="cursor-blink">|</span>
      </div>

      <div class="detail-output" v-if="detail.output">
        <div v-if="detail.output.weather_summary" class="section-card">
          <h4><el-icon><PartlyCloudy /></el-icon>天气预警</h4>
          <p>{{ detail.output.weather_summary }}</p>
        </div>
        <div v-if="detail.output.route_summary" class="section-card">
          <h4><el-icon><Guide /></el-icon>路线建议</h4>
          <p>{{ detail.output.route_summary }}</p>
        </div>
        <div v-if="amapRouteUrl || routeMapImage" class="section-card">
          <h4><el-icon><Location /></el-icon>高德路线</h4>
          <img v-if="routeMapImage" :src="routeMapImage" class="route-map-img" alt="路线图" />
          <a v-if="amapRouteUrl" :href="amapRouteUrl" target="_blank" class="amap-link">打开高德路线 →</a>
        </div>
        <div v-if="detail.output.attractions_summary" class="section-card">
          <h4><el-icon><Place /></el-icon>途径景点</h4>
          <p>{{ detail.output.attractions_summary }}</p>
        </div>
        <div v-if="detail.output.realtime_info_summary" class="section-card realtime-card">
          <h4><el-icon><Connection /></el-icon>实时信息</h4>
          <div class="realtime-markdown" v-html="renderedRealtimeSummary"></div>
        </div>
        <div v-if="detail.output.final_markdown" class="section-card markdown">
          <div v-html="renderedMarkdown"></div>
        </div>
      </div>

      <div v-if="recordStatus === 'canceled'" class="section-card muted-card">
        该记录已取消，不会自动续接生成。
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  Connection,
  Guide,
  Loading,
  Location,
  PartlyCloudy,
  Place,
  Refresh,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { planningApi } from '@/api/planning'
import { useLoading } from '@/composables/useLoading'
import { createStreamClient } from '@/utils/stream'
import { marked } from 'marked'

const route = useRoute()
const router = useRouter()
const { loading, withLoading } = useLoading()
const detail = ref(null)
const streaming = ref(false)
const streamTokens = ref('')
const streamErrorMessage = ref('')
const currentStageName = ref('')
const consumedSequence = ref(0)
const activeStreamRecordId = ref(null)
let streamClient = null
let streamRunId = 0
let intentionalStop = false
let reconnectTimer = null

const statusMap = { pending: '等待中', streaming: '生成中', completed: '已完成', failed: '失败', canceled: '已取消' }
const transportMap = { driving: '自驾', transit: '公共交通', walking: '步行', cycling: '骑行', motorcycle: '摩托车', mixed: '混合出行' }

function statusLabel(s) { return statusMap[s] || s }
function transportLabel(t) { return transportMap[t] || t }

const recordStatus = computed(() => detail.value?.record?.status || '')
const renderedMarkdown = computed(() => {
  if (detail.value?.output?.final_markdown) {
    return marked.parse(detail.value.output.final_markdown)
  }
  return ''
})
const renderedTokens = computed(() => marked.parse(streamTokens.value))
const renderedRealtimeSummary = computed(() => {
  const summary = detail.value?.output?.realtime_info_summary
  return summary ? marked.parse(summary) : ''
})

const latestMapExport = computed(() => detail.value?.snapshots?.map_exports?.[0] || null)
const routeMapImage = computed(() => latestMapExport.value?.image_url || routeMap.value?.image_url || '')
const amapRouteUrl = computed(() => (
  detail.value?.output?.amap_route_url
  || routeMap.value?.amap_route_url
  || latestMapExport.value?.amap_route_url
  || ''
))
const routeMap = ref(null)

const fetchDetail = withLoading(async () => {
  const res = await planningApi.getRecordDetail(route.params.recordId)
  detail.value = res.data
  streamErrorMessage.value = firstErrorMessage(res.data?.errors) || ''
})

async function fetchRouteMap(id = route.params.recordId) {
  try {
    const res = await planningApi.getRouteMap(id)
    routeMap.value = res.data || null
  } catch { /* optional route map fallback */ }
}

function firstErrorMessage(errors = []) {
  const first = errors[0]
  return first?.message || first?.error_message || ''
}

function patchOutput(values) {
  detail.value.output = {
    ...(detail.value.output || {}),
    ...values,
  }
}

function handleSnapshot(data) {
  updateActiveRecordId(data.record_id)
  const payload = data.data || {}
  if (data.type === 'weather') {
    patchOutput({ weather_summary: payload.weather_summary || payload.summary || detail.value.output?.weather_summary || '' })
  } else if (data.type === 'route') {
    patchOutput({ route_summary: payload.route_summary || detail.value.output?.route_summary || '' })
  } else if (data.type === 'transport') {
    patchOutput({ transport_summary: payload.transport_summary || detail.value.output?.transport_summary || '' })
  } else if (data.type === 'map_export') {
    const currentExports = detail.value.snapshots?.map_exports || []
    detail.value.snapshots = {
      ...(detail.value.snapshots || {}),
      map_exports: [{ ...payload }, ...currentExports],
    }
    if (payload.amap_route_url) patchOutput({ amap_route_url: payload.amap_route_url })
  } else if (data.type === 'attractions') {
    patchOutput({ attractions_summary: payload.attractions_summary || detail.value.output?.attractions_summary || '' })
  } else if (data.type === 'realtime') {
    patchOutput({ realtime_info_summary: payload.realtime_info_summary || detail.value.output?.realtime_info_summary || '' })
  } else if (data.type === 'summary') {
    patchOutput({ final_markdown: payload.final_markdown || detail.value.output?.final_markdown || '' })
  }
}

function createRecordStream(url, method = 'GET', body) {
  const runId = ++streamRunId
  return createStreamClient({
    url,
    method,
    body,
    afterSequence: consumedSequence.value,
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
    onRecordCreated(data) {
      updateActiveRecordId(data.record_id)
    },
    onStage(data) {
      updateActiveRecordId(data.record_id)
      currentStageName.value = data.stage_name || data.stage || ''
      if (detail.value?.record) {
        detail.value.record.status = data.status || 'streaming'
        detail.value.record.current_stage = data.stage
      }
    },
    onToken(data) {
      updateActiveRecordId(data.record_id)
      streamTokens.value += data.content || ''
    },
    onSnapshot: handleSnapshot,
    onDone(data) {
      updateActiveRecordId(data.record_id)
      streaming.value = false
      if (detail.value?.record) {
        detail.value.record.status = data.status || 'completed'
        detail.value.record.duration_ms = data.duration_ms || detail.value.record.duration_ms
      }
      if (data.status === 'failed') {
        streamErrorMessage.value = data.message || '生成失败'
      }
      refreshTerminalDetail(activeStreamRecordId.value || route.params.recordId, { replaceRoute: true })
    },
    onError(data) {
      updateActiveRecordId(data.record_id)
      streaming.value = false
      streamErrorMessage.value = data.message || '生成失败'
      if (detail.value?.record) detail.value.record.status = 'failed'
      refreshTerminalDetail(activeStreamRecordId.value || route.params.recordId, { replaceRoute: true })
    },
    onSequence(sequence) {
      consumedSequence.value = sequence
    },
    onClose() {
      streaming.value = false
      if (
        runId === streamRunId
        && !intentionalStop
        && shouldResumeRecord(detail.value?.record?.status)
      ) {
        reconnectTimer = window.setTimeout(() => resumeStream(consumedSequence.value), 1500)
      }
    },
  })
}

async function resumeStream(afterSequence = consumedSequence.value) {
  intentionalStop = false
  consumedSequence.value = afterSequence
  streaming.value = true
  streamErrorMessage.value = ''
  const streamRecordId = activeStreamRecordId.value || route.params.recordId
  streamClient = createRecordStream('', 'GET')
  try {
    const response = await planningApi.resumeRecordStream(streamRecordId, afterSequence)
    await streamClient.connectResponse(response)
  } catch (error) {
    if (intentionalStop) return
    streaming.value = false
    streamErrorMessage.value = error.message || '续接生成失败'
    ElMessage.error(streamErrorMessage.value)
    fetchDetail()
  }
}

async function handleRetry() {
  stopStream()
  intentionalStop = false
  streaming.value = true
  streamTokens.value = ''
  streamErrorMessage.value = ''
  consumedSequence.value = 0
  activeStreamRecordId.value = null
  const url = `${import.meta.env.VITE_API_BASE_URL}/api/v1/planning/records/${route.params.recordId}/retry`
  streamClient = createRecordStream(url, 'POST')
  try {
    await streamClient.connect()
  } catch (error) {
    streaming.value = false
    streamErrorMessage.value = error.message || '重试失败'
    ElMessage.error(streamErrorMessage.value)
    fetchDetail()
  }
}

function stopStream() {
  intentionalStop = true
  streamRunId += 1
  if (reconnectTimer) {
    window.clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  streamClient?.abort()
  streamClient = null
  streaming.value = false
}

function updateActiveRecordId(id) {
  if (id) activeStreamRecordId.value = id
}

async function refreshTerminalDetail(id, options = {}) {
  try {
    const res = await planningApi.getRecordDetail(id)
    detail.value = res.data
    fetchRouteMap(id)
    if (options.replaceRoute && Number(id) !== Number(route.params.recordId)) {
      router.replace(`/history/${id}`)
    }
  } catch { /* keep current stream-rendered state */ }
}

async function initialize() {
  stopStream()
  routeMap.value = null
  streamTokens.value = ''
  currentStageName.value = ''
  consumedSequence.value = 0
  activeStreamRecordId.value = Number(route.params.recordId)
  await fetchDetail()
  fetchRouteMap()
  if (shouldResumeRecord(recordStatus.value)) {
    resumeStream(0)
  }
}

function shouldResumeRecord(status) {
  return status === 'streaming' || status === 'pending'
}

watch(() => route.params.recordId, () => initialize())

onMounted(() => initialize())
onBeforeUnmount(() => stopStream())
</script>

<style lang="scss" scoped>
.detail-page {
  max-width: 720px;
  margin: 0 auto;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: $text-secondary;
  font-size: $font-size-sm;
  cursor: pointer;
  padding: 8px 0;
  margin-bottom: 8px;

  &:hover { color: $text-primary; }
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;

  h2 {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 12px;
    line-height: 1.35;
  }
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-badge {
  font-size: $font-size-xs;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;

  &.completed { background: rgba($color-success, 0.1); color: $color-success; }
  &.streaming { background: $color-primary-bg; color: $color-primary; }
  &.failed { background: rgba($color-danger, 0.1); color: $color-danger; }
  &.pending, &.canceled { background: $page-bg; color: $text-secondary; }
}

.info-tag {
  font-size: $font-size-xs;
  padding: 4px 12px;
  border-radius: 12px;
  background: $page-bg;
  color: $text-secondary;
}

.retry-btn,
.stop-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.retry-btn {
  flex: 0 0 auto;
  padding: 9px 16px;
  color: #fff;
  background: $color-primary;
  border-radius: 18px;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.stop-btn {
  margin-left: auto;
  padding: 5px 12px;
  color: $color-danger;
  background: rgba($color-danger, 0.08);
  border-radius: 999px;
}

.section-card {
  min-width: 0;
  background: $content-bg;
  border-radius: $radius-lg;
  padding: 20px 24px;
  margin-bottom: 12px;
  box-shadow: $shadow-card;
  overflow-wrap: anywhere;
  word-break: break-word;

  h4 {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 15px;
    font-weight: 600;
    color: $text-secondary;
    margin-bottom: 10px;

    .el-icon {
      color: $color-primary;
      font-size: 17px;
    }
  }

  p {
    line-height: 1.7;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
}

.process-card {
  background: rgba($content-bg, 0.9);
}

.process-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;

  h4 {
    margin-bottom: 0;
  }
}

.stage-pill {
  font-size: $font-size-xs;
  color: $color-primary;
  background: $color-primary-bg;
  border-radius: 999px;
  padding: 3px 10px;
}

.error-text {
  color: $color-danger;
}

.stream-tokens {
  line-height: 1.8;
}

.cursor-blink {
  color: $color-primary;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.amap-link {
  color: $color-link;
  font-weight: 500;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.route-map-img {
  width: 100%;
  border-radius: $radius-sm;
  border: 1px solid $border-light;
  margin-bottom: 10px;
}

.markdown :deep(h2) { font-size: 18px; margin: 16px 0 8px; }
.markdown :deep(p),
.stream-tokens :deep(p),
.realtime-markdown :deep(p) {
  margin-bottom: 10px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.markdown :deep(a),
.stream-tokens :deep(a),
.realtime-markdown :deep(a) {
  overflow-wrap: anywhere;
  word-break: break-word;
}

.markdown :deep(ul),
.markdown :deep(ol),
.stream-tokens :deep(ul),
.stream-tokens :deep(ol),
.realtime-markdown :deep(ul),
.realtime-markdown :deep(ol) {
  padding-left: 20px;
  margin-bottom: 10px;
}

.markdown :deep(li),
.stream-tokens :deep(li),
.realtime-markdown :deep(li) {
  margin-bottom: 4px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.muted-card {
  color: $text-secondary;
  font-size: $font-size-sm;
}

@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
  }
}
</style>
