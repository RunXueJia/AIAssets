<template>
  <div class="planning-page">
    <!-- Input Panel - Step Wizard -->
    <aside class="input-panel">
      <!-- Step Indicator -->
      <div class="step-indicator">
        <button
          v-for="(s, i) in stepDefs"
          :key="s.key"
          class="step-dot-nav"
          :class="{ done: i < currentStep, active: i === currentStep }"
          :disabled="i > currentStep"
          @click="i < currentStep && goToStep(i)"
        >
          <span class="dot-circle">{{ i < currentStep ? '✓' : i + 1 }}</span>
          <span class="dot-label">{{ s.label }}</span>
        </button>
      </div>

      <!-- Step Content -->
      <div class="step-body" :key="currentStep">
        <transition name="step-fade" mode="out-in">
          <!-- Step 0: Where -->
          <div v-if="currentStep === 0" key="where" class="step-content">
            <div class="step-emoji">📍</div>
            <h3 class="step-title">去哪儿？</h3>
            <p class="step-desc">告诉我们起点和目的地</p>
            <div class="step-form">
              <div class="input-group">
                <label class="input-label">起点</label>
                <el-input
                  v-model="form.origin"
                  placeholder="城市、地址或地标"
                  maxlength="100"
                  size="large"
                  :class="{ error: errors.origin }"
                  @input="errors.origin = ''"
                />
                <span v-if="errors.origin" class="field-error">{{ errors.origin }}</span>
              </div>
              <div class="input-group">
                <label class="input-label">目的地</label>
                <el-input
                  v-model="form.destination"
                  placeholder="想去哪里？"
                  maxlength="100"
                  size="large"
                  :class="{ error: errors.destination }"
                  @input="errors.destination = ''"
                />
                <span v-if="errors.destination" class="field-error">{{ errors.destination }}</span>
              </div>
              <div class="input-group">
                <label class="input-label">范围</label>
                <el-input
                  v-model="form.range"
                  placeholder="例如：一天、步行少一点"
                  maxlength="200"
                  size="large"
                  :class="{ error: errors.range }"
                  @input="errors.range = ''"
                />
                <span v-if="errors.range" class="field-error">{{ errors.range }}</span>
              </div>
            </div>
          </div>

          <!-- Step 1: Transport -->
          <div v-else-if="currentStep === 1" key="how" class="step-content">
            <div class="step-emoji">🚗</div>
            <h3 class="step-title">怎么去？</h3>
            <p class="step-desc">选择出行方式</p>
            <div class="transport-grid">
              <button
                v-for="opt in transportOptions"
                :key="opt.value"
                type="button"
                class="transport-card"
                :class="{ active: form.transport_mode === opt.value }"
                @click="form.transport_mode = opt.value"
              >
                <component :is="opt.icon" class="t-icon" />
                <span class="t-label">{{ opt.label }}</span>
                <span class="t-desc">{{ opt.desc }}</span>
              </button>
            </div>
          </div>

          <!-- Step 2: When & People -->
          <div v-else-if="currentStep === 2" key="when" class="step-content">
            <div class="step-emoji">📅</div>
            <h3 class="step-title">什么时候？</h3>
            <p class="step-desc">选填，不填也可以生成</p>
            <div class="step-form">
              <div class="input-group">
                <label class="input-label">出行日期</label>
                <el-date-picker
                  v-model="form.travel_date"
                  type="date"
                  placeholder="选填"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                  size="large"
                />
              </div>
              <div class="input-group">
                <label class="input-label">人数</label>
                <div class="people-picker">
                  <button class="people-btn" @click="form.people_count > 1 && form.people_count--">−</button>
                  <span class="people-num">{{ form.people_count }}</span>
                  <button class="people-btn" @click="form.people_count < 20 && form.people_count++">+</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3: Preferences -->
          <div v-else-if="currentStep === 3" key="pref" class="step-content">
            <div class="step-emoji">🎯</div>
            <h3 class="step-title">偏好与避开</h3>
            <p class="step-desc">告诉我们你的喜好</p>
            <div class="step-form">
              <div class="input-group">
                <label class="input-label">偏好</label>
                <div class="tag-grid">
                  <span
                    v-for="p in preferenceOptions"
                    :key="p"
                    class="tag-item"
                    :class="{ active: form.preferences.includes(p) }"
                    @click="togglePreference(p)"
                  >{{ p }}</span>
                </div>
              </div>
              <div class="input-group">
                <label class="input-label">避开</label>
                <div class="tag-grid">
                  <span
                    v-for="a in avoidanceOptions"
                    :key="a"
                    class="tag-item avoid-tag"
                    :class="{ active: form.avoidances.includes(a) }"
                    @click="toggleAvoidance(a)"
                  >{{ a }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 4: Confirm -->
          <div v-else-if="currentStep === 4" key="confirm" class="step-content">
            <div class="step-emoji">✨</div>
            <h3 class="step-title">确认信息</h3>
            <p class="step-desc">确认无误后开始生成</p>
            <div class="confirm-cards">
              <div class="confirm-item">
                <span class="ci-label">📍 去哪儿</span>
                <span class="ci-val">{{ form.origin }} → {{ form.destination }}</span>
                <span class="ci-sub">{{ form.range }}</span>
              </div>
              <div class="confirm-item">
                <span class="ci-label">🚗 怎么去</span>
                <span class="ci-val">{{ transportOptions.find(o => o.value === form.transport_mode)?.label }}</span>
              </div>
              <div class="confirm-item" v-if="form.travel_date || form.people_count > 1">
                <span class="ci-label">📅 出行信息</span>
                <span class="ci-val">
                  {{ form.travel_date ? form.travel_date + ' · ' : '' }}{{ form.people_count }}人
                </span>
              </div>
              <div class="confirm-item" v-if="form.preferences.length">
                <span class="ci-label">🎯 偏好</span>
                <span class="ci-val">{{ form.preferences.join('、') }}</span>
              </div>
              <div class="confirm-item" v-if="form.avoidances.length">
                <span class="ci-label">避开</span>
                <span class="ci-val">{{ form.avoidances.join('、') }}</span>
              </div>
            </div>

            <button
              type="button"
              class="generate-btn"
              :class="{ loading: streaming }"
              :disabled="streaming"
              @click="handleGenerate"
            >
              <span v-if="streaming">
                <span class="dot-pulse"></span>生成中...
              </span>
              <span v-else>✨ 开始生成</span>
            </button>
          </div>
        </transition>
      </div>

      <!-- Step Nav Buttons -->
      <div class="step-nav" v-if="currentStep < 4">
        <button
          v-if="currentStep > 0"
          class="nav-btn back"
          @click="goToStep(currentStep - 1)"
        >
          ← 上一步
        </button>
        <div v-else class="nav-spacer"></div>
        <button class="nav-btn next" @click="handleNext">
          {{ currentStep === 3 ? '确认信息' : '下一步' }} →
        </button>
      </div>
    </aside>

    <!-- Output Panel - unchanged -->
    <section class="output-panel" ref="outputPanel">
      <template v-if="streaming || outputState">
        <div class="stream-status-bar">
          <div class="status-left">
            <span class="status-dot" :class="streaming ? 'streaming' : outputState?.status"></span>
            <span class="status-text">{{ statusLabel }}</span>
            <span v-if="currentStageName" class="stage-badge">{{ currentStageName }}</span>
            <span v-if="duration" class="duration">{{ duration }}</span>
          </div>
          <div class="status-right">
            <button v-if="streaming" class="action-btn stop" @click="handleCancel">停止生成</button>
            <button v-if="!streaming && outputState?.status === 'completed'" class="action-btn copy" @click="copyResult">复制结果</button>
          </div>
        </div>
        <div class="stage-steps" v-if="stages.length">
          <div v-for="s in stages" :key="s.key" class="step-item" :class="{ active: s.active, done: s.done }">
            <span class="step-dot"></span>
            <span class="step-label">{{ s.label }}</span>
          </div>
        </div>
        <div class="stream-content" ref="streamContent">
          <div v-if="streamErrorMessage" class="content-card error-card">
            <div class="card-label">生成失败</div>
            <p>{{ streamErrorMessage }}</p>
          </div>
          <div v-if="weatherSummary" class="content-card weather-card">
            <div class="card-label">☁️ 天气预警</div>
            <p>{{ weatherSummary }}</p>
            <div v-if="weatherMeta" class="source-meta">{{ weatherMeta }}</div>
          </div>
          <div v-if="routeSummary" class="content-card route-card">
            <div class="card-label">🗺 路线建议</div>
            <p>{{ routeSummary }}</p>
          </div>
          <div v-if="transportSummary" class="content-card transport-card">
            <div class="card-label">🚇 交通建议</div>
            <p>{{ transportSummary }}</p>
          </div>
          <div v-if="amapUrl || routeMapImage" class="content-card map-card">
            <div class="card-label">📍 高德路线图</div>
            <img v-if="routeMapImage" :src="routeMapImage" class="route-map-img" alt="路线图" />
            <div v-if="mapMeta" class="source-meta">{{ mapMeta }}</div>
            <div class="map-actions">
              <a v-if="amapUrl" :href="amapUrl" target="_blank" class="amap-link">打开高德路线 →</a>
              <button v-if="routeMapImage" class="download-btn" @click.stop="downloadRouteMap">💾 保存路线图</button>
            </div>
          </div>
          <div v-if="attractionsSummary" class="content-card attr-card">
            <div class="card-label">🏞 途径景点</div>
            <p>{{ attractionsSummary }}</p>
          </div>
          <div v-if="realtimeSummary" class="content-card realtime-card">
            <div class="card-label">📡 实时信息</div>
            <p>{{ realtimeSummary }}</p>
            <div v-if="realtimeMeta" class="source-meta">{{ realtimeMeta }}</div>
          </div>
          <div v-if="streamTokens" class="stream-tokens" v-html="renderedTokens"></div>
          <div v-if="finalMarkdown" class="final-markdown" v-html="renderedMarkdown"></div>
          <span v-if="streaming" class="cursor-blink">|</span>
        </div>
      </template>
      <div v-else class="output-empty">
        <div class="empty-illustration">🗺</div>
        <p class="empty-title">准备好出发了吗？</p>
        <p class="empty-desc">填写信息后，AI 将分析天气、路线、景点和实时信息，为你定制出行计划</p>
        <div class="empty-features">
          <span class="feat-item">☁️ 天气预警</span>
          <span class="feat-item">🗺 路线规划</span>
          <span class="feat-item">🏞 景点推荐</span>
          <span class="feat-item">📡 实时资讯</span>
        </div>
      </div>
    </section>

    <!-- Recent history records below output -->
    <div v-if="recentRecords.length && !streaming" class="recent-records">
      <div class="recent-header">
        <h4>最近的规划记录</h4>
        <button class="view-all-link" @click="$router.push('/history')">查看全部 →</button>
      </div>
      <div class="recent-grid">
        <div
          v-for="item in recentRecords"
          :key="item.id"
          class="recent-card"
          @click="$router.push(`/history/${item.id}`)"
        >
          <div class="rc-route">
            <span class="rc-place">{{ item.origin_text }}</span>
            <span class="rc-arrow">→</span>
            <span class="rc-place">{{ item.destination_text }}</span>
          </div>
          <div class="rc-meta">
            <span class="rc-transport">{{ getTransportLabel(item.transport_mode) }}</span>
            <span class="rc-status" :class="item.status">{{ getStatusLabel(item.status) }}</span>
            <span class="rc-time">{{ formatRelative(item.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Van, Guide, User, Bicycle, Connection } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { planningApi } from '@/api/planning'
import { createStreamClient } from '@/utils/stream'
import { marked } from 'marked'

import dayjs from 'dayjs'

const auth = useAuthStore()
const streamContent = ref(null)

// Wizard state
const currentStep = ref(0)
const stepDefs = [
  { key: 'where', label: '去哪儿' },
  { key: 'how', label: '怎么去' },
  { key: 'when', label: '什么时候' },
  { key: 'pref', label: '偏好' },
  { key: 'confirm', label: '确认' },
]

const form = reactive({
  origin: '',
  destination: '',
  range: '',
  transport_mode: 'mixed',
  travel_date: '',
  people_count: 1,
  preferences: [],
  avoidances: [],
})

const errors = reactive({ origin: '', destination: '', range: '' })

const transportOptions = [
  { value: 'driving', label: '自驾', desc: '灵活自由', icon: Van },
  { value: 'transit', label: '公交', desc: '地铁公交', icon: Guide },
  { value: 'walking', label: '步行', desc: '慢行探索', icon: User },
  { value: 'cycling', label: '骑行', desc: '健康环保', icon: Bicycle },
  { value: 'mixed', label: '混合', desc: '智能搭配', icon: Connection },
]

const preferenceOptions = ['自然风光', '人文历史', '亲子友好', '美食探店', '小众路线', '低强度', '咖啡']
const avoidanceOptions = ['不走高速', '少换乘', '少步行', '避开热门', '避开收费']

const statusMap = { pending: '等待中', streaming: '生成中', completed: '已完成', failed: '失败', canceled: '已取消' }
const transportMap = { driving: '自驾', transit: '公交', walking: '步行', cycling: '骑行', mixed: '混合' }
function getStatusLabel(s) { return statusMap[s] || s }
function getTransportLabel(t) { return transportMap[t] || t }

function formatRelative(t) {
  if (!t) return ''
  const d = dayjs(t)
  const now = dayjs()
  const mins = now.diff(d, 'minute')
  if (mins < 1) return '刚刚'
  if (mins < 60) return mins + '分钟前'
  const hours = now.diff(d, 'hour')
  if (hours < 24) return hours + '小时前'
  const days = now.diff(d, 'day')
  if (days < 7) return days + '天前'
  return ''
}

function validateStep(step) {
  if (step === 0) {
    errors.origin = form.origin.trim() ? '' : '请输入起点'
    errors.destination = form.destination.trim() ? '' : '请输入目的地'
    errors.range = form.range.trim() ? '' : '请输入出行范围'
    return !errors.origin && !errors.destination && !errors.range
  }
  if (step === 1) return !!form.transport_mode
  return true
}

function handleNext() {
  if (!validateStep(currentStep.value)) return
  if (currentStep.value < 4) {
    currentStep.value++
  }
}

function goToStep(step) {
  currentStep.value = step
}

function togglePreference(p) {
  const idx = form.preferences.indexOf(p)
  if (idx >= 0) form.preferences.splice(idx, 1)
  else form.preferences.push(p)
}

function toggleAvoidance(a) {
  const idx = form.avoidances.indexOf(a)
  if (idx >= 0) form.avoidances.splice(idx, 1)
  else form.avoidances.push(a)
}

// Streaming
const streaming = ref(false)
const currentStage = ref('')
const currentStageName = ref('')
const streamTokens = ref('')
const weatherSummary = ref('')
const weatherSource = ref(null)
const routeSummary = ref('')
const transportSummary = ref('')
const amapUrl = ref('')
const routeMapImage = ref('')
const mapSource = ref(null)
const attractionsSummary = ref('')
const realtimeSummary = ref('')
const realtimeSource = ref(null)
const finalMarkdown = ref('')
const streamErrorMessage = ref('')
const duration = ref('')
const recordId = ref(null)
const outputState = ref(null)
const recentRecords = ref([])

const stages = reactive([
  { key: 'understanding', label: '理解需求', active: false, done: false },
  { key: 'weather', label: '天气', active: false, done: false },
  { key: 'route', label: '路线', active: false, done: false },
  { key: 'transport', label: '交通', active: false, done: false },
  { key: 'map_export', label: '地图', active: false, done: false },
  { key: 'attractions', label: '景点', active: false, done: false },
  { key: 'realtime', label: '实时信息', active: false, done: false },
  { key: 'summary', label: '汇总', active: false, done: false },
])

const statusLabel = computed(() => {
  if (streaming.value) return '正在生成'
  if (outputState.value?.status === 'completed') return '生成完成'
  if (outputState.value?.status === 'failed') return '生成失败'
  if (outputState.value?.status === 'canceled') return '已取消'
  return ''
})

const renderedTokens = computed(() => marked.parse(streamTokens.value))
const renderedMarkdown = computed(() => finalMarkdown.value ? marked.parse(finalMarkdown.value) : '')
const weatherMeta = computed(() => formatSourceMeta(weatherSource.value))
const mapMeta = computed(() => formatSourceMeta(mapSource.value))
const realtimeMeta = computed(() => formatSourceMeta(realtimeSource.value))

let streamClient = null

function buildSourceMeta(data) {
  if (!data) return null
  return {
    provider: data.provider,
    source_updated_at: data.source_updated_at,
    mock: data.mock,
  }
}

function formatSourceMeta(meta) {
  if (!meta) return ''
  const parts = []
  if (meta.provider) parts.push(`来源：${meta.provider}`)
  if (meta.source_updated_at) parts.push(`更新：${meta.source_updated_at}`)
  if (meta.mock === true) parts.push('Mock 数据')
  else if (meta.mock === false) parts.push('真实数据')
  return parts.join(' · ')
}

function failGeneration(message, data = {}) {
  streaming.value = false
  streamErrorMessage.value = message || '生成失败'
  outputState.value = { status: 'failed' }
  if (data.duration_ms) duration.value = `${(data.duration_ms / 1000).toFixed(1)}s`
  stages.forEach(s => { s.active = false })
  ElMessage.error(streamErrorMessage.value)
}

async function handleGenerate() {
  if (!auth.isAuthenticated) await auth.initGuestSession()

  resetOutput()
  streaming.value = true

  const body = {
    origin: form.origin,
    destination: form.destination,
    range: form.range,
    transport_mode: form.transport_mode,
    travel_date: form.travel_date || undefined,
    people_count: form.people_count,
    preferences: form.preferences.length ? form.preferences : undefined,
    avoidances: form.avoidances.length ? form.avoidances : undefined,
  }

  const token = auth.token
  streamClient = createStreamClient(
    `${import.meta.env.VITE_API_BASE_URL}/api/v1/planning/generate_stream`,
    {
      headers: { Authorization: `Bearer ${token}` },
      onRecordCreated(data) { recordId.value = data.record_id },
      onStage(data) {
        currentStage.value = data.stage
        currentStageName.value = data.stage_name
        setStageActive(data.stage)
      },
      onToken(data) { streamTokens.value += data.content; autoScroll() },
      onSnapshot(data) {
        if (data.type === 'weather') {
          weatherSummary.value = data.data?.weather_summary || data.data?.summary || ''
          weatherSource.value = buildSourceMeta(data.data)
        }
        else if (data.type === 'route') routeSummary.value = data.data?.route_summary || ''
        else if (data.type === 'transport') transportSummary.value = data.data?.transport_summary || ''
        else if (data.type === 'map_export') {
          amapUrl.value = data.data?.amap_route_url || ''
          routeMapImage.value = data.data?.image_url || data.data?.route_map_image || ''
          mapSource.value = buildSourceMeta(data.data)
        }
        else if (data.type === 'attractions') attractionsSummary.value = data.data?.attractions_summary || ''
        else if (data.type === 'realtime') {
          realtimeSummary.value = data.data?.realtime_info_summary || ''
          realtimeSource.value = buildSourceMeta(data.data)
        }
        else if (data.type === 'summary') finalMarkdown.value = data.data?.final_markdown || ''
      },
      onDone(data) {
        streaming.value = false
        outputState.value = { status: data.status || 'completed' }
        duration.value = data.duration_ms ? `${(data.duration_ms / 1000).toFixed(1)}s` : ''
        stages.forEach(s => { s.done = data.status === 'completed'; s.active = false })
        if (data.status === 'failed') {
          if (!streamErrorMessage.value) {
            streamErrorMessage.value = data.message || '生成失败'
            ElMessage.error(streamErrorMessage.value)
          }
        }
        if (data.record_id) loadRecordDetail(data.record_id)
        fetchRecentRecords()
      },
      onError(data) {
        failGeneration(data.message || '生成失败', data)
      },
      onClose() { streaming.value = false },
    },
  )

  try {
    await streamClient.connect(body)
  } catch (error) {
    failGeneration(error.message || '连接失败，请重试')
  }
}

function handleCancel() {
  if (recordId.value) planningApi.cancel(recordId.value).catch(() => {})
  streamClient?.abort()
  streaming.value = false
  outputState.value = { status: 'canceled' }
}

async function loadRecordDetail(id) {
  try {
    const res = await planningApi.getRecordDetail(id)
    const output = res.data?.output
    if (output) {
      if (output.final_markdown) finalMarkdown.value = output.final_markdown
      if (output.weather_summary) weatherSummary.value = output.weather_summary
      if (output.route_summary) routeSummary.value = output.route_summary
      if (output.amap_route_url) amapUrl.value = output.amap_route_url
      if (output.image_url) routeMapImage.value = output.image_url
      if (output.attractions_summary) attractionsSummary.value = output.attractions_summary
      if (output.realtime_info_summary) realtimeSummary.value = output.realtime_info_summary
    }
    const weatherSnapshot = res.data?.snapshots?.weather?.[0]
    if (weatherSnapshot) weatherSource.value = buildSourceMeta(weatherSnapshot)
    const mapExport = res.data?.snapshots?.map_exports?.[0]
    if (mapExport) {
      amapUrl.value = mapExport.amap_route_url || amapUrl.value
      routeMapImage.value = mapExport.image_url || routeMapImage.value
      mapSource.value = buildSourceMeta(mapExport)
    }
    const realtimeSnapshots = res.data?.snapshots?.realtime_info || {}
    const realtimeItems = [
      ...(realtimeSnapshots.news_traffic || []),
      ...(realtimeSnapshots.guide_pitfall || []),
    ]
    if (realtimeItems.length) realtimeSource.value = buildSourceMeta(realtimeItems[0])
  } catch { /* non-critical */ }
}

function setStageActive(key) {
  const idx = stages.findIndex(s => s.key === key)
  if (idx >= 0) {
    stages.forEach(s => { s.active = false; s.done = false })
    for (let i = 0; i < idx; i++) stages[i].done = true
    stages[idx].active = true
  }
}

function resetOutput() {
  streamTokens.value = ''
  weatherSummary.value = ''
  weatherSource.value = null
  routeSummary.value = ''
  transportSummary.value = ''
  amapUrl.value = ''
  routeMapImage.value = ''
  mapSource.value = null
  attractionsSummary.value = ''
  realtimeSummary.value = ''
  realtimeSource.value = null
  finalMarkdown.value = ''
  streamErrorMessage.value = ''
  duration.value = ''
  recordId.value = null
  outputState.value = null
  stages.forEach(s => { s.active = false; s.done = false })
}

function autoScroll() {
  nextTick(() => {
    if (streamContent.value) {
      streamContent.value.scrollTop = streamContent.value.scrollHeight
    }
  })
}

function copyResult() {
  const text = finalMarkdown.value || streamTokens.value
  if (text) {
    navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  }
}

async function fetchRecentRecords() {
  try {
    const res = await planningApi.getRecords({ page: 1, page_size: 6, status: 'completed' })
    recentRecords.value = res.data?.items || []
  } catch { /* keep stale list */ }
}

async function downloadRouteMap() {
  const url = routeMapImage.value
  if (!url) return
  try {
    const res = await fetch(url)
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `route_map_${recordId.value || Date.now()}.png`
    a.click()
    URL.revokeObjectURL(a.href)
    ElMessage.success('路线图已开始下载')
  } catch {
    ElMessage.error('下载失败，请重试')
  }
}

onMounted(async () => {
  if (!auth.isAuthenticated) await auth.initGuestSession()
})
</script>

<style lang="scss" scoped>
.planning-page {
  display: flex;
  gap: 24px;
  height: calc(100vh - $nav-height - 40px);
  align-items: flex-start;
}

// INPUT PANEL
.input-panel {
  width: $input-panel-width;
  flex-shrink: 0;
  background: $content-bg;
  border-radius: $radius-xl;
  box-shadow: $shadow-card;
  display: flex;
  flex-direction: column;
  max-height: 100%;
  overflow: hidden;
}

// Step Indicator
.step-indicator {
  display: flex;
  justify-content: center;
  gap: 0;
  padding: 20px 16px 12px;
  border-bottom: 0.5px solid $border-card;
  flex-shrink: 0;
}

.step-dot-nav {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0 12px;
  min-width: 52px;
  transition: opacity 0.2s;

  &:disabled { cursor: default; opacity: 0.35; }
}

.dot-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  background: $page-bg;
  color: $text-hint;
  transition: all 0.3s;

  .done & {
    background: $color-success;
    color: #fff;
  }

  .active & {
    background: $color-primary;
    color: #fff;
    box-shadow: 0 2px 8px rgba($color-primary, 0.3);
  }
}

.dot-label {
  font-size: 10px;
  color: $text-hint;
  white-space: nowrap;
  transition: color 0.2s;

  .done &, .active & {
    color: $text-primary;
    font-weight: 500;
  }
}

// Step Body
.step-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.step-content {
  padding: 0 24px;
}

.step-emoji {
  font-size: 40px;
  text-align: center;
  margin-bottom: 8px;
}

.step-title {
  font-size: 20px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 4px;
}

.step-desc {
  font-size: $font-size-sm;
  color: $text-secondary;
  text-align: center;
  margin-bottom: 24px;
}

.step-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-label {
  font-size: $font-size-sm;
  font-weight: 600;
  color: $text-primary;
}

.field-error {
  font-size: $font-size-xs;
  color: $color-danger;
}

.input-group :deep(.el-input__wrapper.error),
.input-group :deep(.error .el-input__wrapper) {
  box-shadow: 0 0 0 2px $color-danger inset !important;
}

// Transport Grid
.transport-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.transport-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border: 1.5px solid $border-light;
  border-radius: $radius-md;
  background: $content-bg;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  width: 100%;

  .t-icon {
    width: 28px;
    height: 28px;
    flex-shrink: 0;
    color: $text-secondary;
    transition: color 0.2s;
  }

  .t-label {
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
  }

  .t-desc {
    font-size: $font-size-xs;
    color: $text-hint;
    margin-left: auto;
  }

  &.active {
    border-color: $color-primary;
    background: $color-primary-bg;

    .t-icon { color: $color-primary; }
    .t-desc { color: $color-primary; }
  }

  &:hover:not(.active) {
    border-color: #d5d5db;
  }
}

// People Picker
.people-picker {
  display: flex;
  align-items: center;
  gap: 0;
  background: $page-bg;
  border-radius: 12px;
  width: fit-content;
}

.people-btn {
  width: 48px;
  height: 48px;
  border: none;
  background: none;
  font-size: 22px;
  color: $color-primary;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;

  &:hover { background: rgba($color-primary, 0.06); }
  &:first-child { border-radius: 12px 0 0 12px; }
  &:last-child { border-radius: 0 12px 12px 0; }
}

.people-num {
  width: 52px;
  text-align: center;
  font-size: 20px;
  font-weight: 700;
  color: $text-primary;
}

// Tags
.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  padding: 8px 16px;
  border: 1.5px solid $border-light;
  border-radius: 20px;
  font-size: $font-size-sm;
  cursor: pointer;
  color: $text-secondary;
  background: $content-bg;
  transition: all 0.2s;
  user-select: none;

  &.active {
    border-color: $color-primary;
    color: $color-primary;
    background: $color-primary-bg;
    font-weight: 500;
  }

  &.avoid-tag.active {
    border-color: $color-danger;
    color: $color-danger;
    background: rgba($color-danger, 0.06);
  }

  &:hover:not(.active) {
    border-color: #d9d9de;
  }
}

// Confirm Cards
.confirm-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 8px;
}

.confirm-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 16px;
  background: $page-bg;
  border-radius: $radius-md;
}

.ci-label {
  font-size: $font-size-xs;
  color: $text-hint;
  font-weight: 500;
}

.ci-val {
  font-size: $font-size-body;
  font-weight: 600;
  color: $text-primary;
}

.ci-sub {
  font-size: $font-size-sm;
  color: $text-secondary;
}

// Generate Button
.generate-btn {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 24px;
  background: linear-gradient(135deg, $color-primary, $color-primary-light);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  letter-spacing: 1px;
  box-shadow: 0 4px 16px rgba($color-primary, 0.3);

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 24px rgba($color-primary, 0.4);
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
}

.dot-pulse {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fff;
  animation: pulse-dot 1s infinite;
  margin-right: 6px;
  vertical-align: middle;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

// Step Navigation
.step-nav {
  display: flex;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 0.5px solid $border-card;
  flex-shrink: 0;
}

.nav-spacer { flex: 1; }

.nav-btn {
  padding: 12px 28px;
  border: none;
  border-radius: 22px;
  font-size: $font-size-body;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &.back {
    background: $page-bg;
    color: $text-secondary;
    &:hover { background: $border-light; }
  }

  &.next {
    background: linear-gradient(135deg, $color-primary, $color-primary-light);
    color: #fff;
    margin-left: auto;
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba($color-primary, 0.3);
    }
  }
}

// Step transition
.step-fade-enter-active,
.step-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.step-fade-enter-from {
  opacity: 0;
  transform: translateX(16px);
}

.step-fade-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}

// OUTPUT PANEL (unchanged)
.output-panel {
  flex: 1;
  background: $content-bg;
  border-radius: $radius-xl;
  box-shadow: $shadow-card;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 560px;
  max-height: 100%;
}

.stream-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 0.5px solid $border-card;
  flex-shrink: 0;
}

.status-left { display: flex; align-items: center; gap: 10px; }

.status-dot {
  width: 9px; height: 9px; border-radius: 50%;
  &.streaming { background: $color-primary; animation: pulse 1.5s infinite; }
  &.completed { background: $color-success; }
  &.failed { background: $color-danger; }
  &.canceled { background: $text-hint; }
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(1.5); }
}

.status-text { font-size: $font-size-sm; font-weight: 500; }
.stage-badge { font-size: $font-size-xs; background: $page-bg; padding: 3px 10px; border-radius: 12px; color: $text-secondary; }
.duration { font-size: $font-size-xs; color: $text-hint; }

.action-btn {
  padding: 6px 18px; border: none; border-radius: 16px; font-size: $font-size-sm; font-weight: 500; cursor: pointer; transition: all 0.2s;
  &.stop { background: rgba($color-danger, 0.1); color: $color-danger; &:hover { background: rgba($color-danger, 0.2); } }
  &.copy { background: $page-bg; color: $text-primary; &:hover { background: $border-light; } }
}

.stage-steps {
  display: flex; flex-wrap: wrap; gap: 4px; padding: 10px 20px; border-bottom: 0.5px solid $border-card;
  flex-shrink: 0;
}

.step-item {
  display: flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 12px;
  font-size: $font-size-xs; color: $text-hint; white-space: nowrap; transition: all 0.2s;
  .step-dot { width: 6px; height: 6px; border-radius: 50%; background: $border-light; transition: all 0.2s; }
  &.active { color: $color-primary; font-weight: 600; background: $color-primary-bg; .step-dot { background: $color-primary; } }
  &.done { color: $color-success; .step-dot { background: $color-success; } }
}

.stream-content {
  flex: 1; overflow-y: auto; padding: 20px 24px; font-size: $font-size-body; line-height: 1.8; color: $text-primary;
}

.content-card {
  background: $page-bg; border-radius: $radius-md; padding: 16px 18px; margin-bottom: 14px;
  .card-label { font-size: $font-size-sm; font-weight: 600; color: $text-secondary; margin-bottom: 8px; }
  p { font-size: $font-size-body; line-height: 1.7; }

  &.error-card {
    background: rgba($color-danger, 0.06);
    border: 1px solid rgba($color-danger, 0.18);

    .card-label,
    p {
      color: $color-danger;
    }
  }
}

.map-card .amap-link { color: $color-link; font-weight: 500; &:hover { text-decoration: underline; } }

.source-meta {
  margin-top: 8px;
  font-size: $font-size-xs;
  color: $text-hint;
  line-height: 1.5;
}

.route-map-img {
  width: 100%;
  border-radius: $radius-sm;
  margin-bottom: 10px;
  border: 1px solid $border-light;
}

.map-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.download-btn {
  border: none;
  background: $color-primary-bg;
  color: $color-primary;
  padding: 6px 14px;
  border-radius: 16px;
  font-size: $font-size-sm;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  &:hover { background: rgba($color-primary, 0.15); }
}

.final-markdown, .stream-tokens {
  :deep(h2) { font-size: 18px; margin: 20px 0 10px; }
  :deep(h3) { font-size: 16px; margin: 16px 0 8px; }
  :deep(p) { margin-bottom: 10px; }
  :deep(ul), :deep(ol) { padding-left: 20px; margin-bottom: 10px; }
  :deep(li) { margin-bottom: 4px; }
}

.cursor-blink { animation: blink 1s infinite; color: $color-primary; font-weight: 300; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

// Empty state
.output-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px 32px; text-align: center;
}
.empty-illustration { font-size: 56px; margin-bottom: 16px; filter: grayscale(0.2); }
.empty-title { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.empty-desc { font-size: $font-size-sm; color: $text-secondary; line-height: 1.6; margin-bottom: 24px; }
.empty-features { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.feat-item { font-size: $font-size-sm; padding: 6px 14px; background: $page-bg; border-radius: 20px; color: $text-secondary; }

// Recent records section
.recent-records {
  margin-top: 24px;
}

.recent-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;

  h4 {
    font-size: 16px;
    font-weight: 600;
  }
}

.view-all-link {
  background: none;
  border: none;
  color: $color-link;
  font-size: $font-size-sm;
  cursor: pointer;
  font-weight: 500;
  &:hover { text-decoration: underline; }
}

.recent-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.recent-card {
  background: $content-bg;
  border-radius: $radius-md;
  padding: 14px 16px;
  box-shadow: $shadow-sm;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    transform: translateY(-1px);
    box-shadow: $shadow-md;
  }
}

.rc-route {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: $font-size-sm;
  margin-bottom: 8px;
}

.rc-place {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100px;
}

.rc-arrow {
  color: $text-hint;
  flex-shrink: 0;
  font-weight: 300;
}

.rc-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rc-transport {
  font-size: $font-size-xs;
  padding: 2px 8px;
  background: $page-bg;
  border-radius: 6px;
  color: $text-secondary;
}

.rc-status {
  font-size: $font-size-xs;
  font-weight: 500;

  &.completed { color: $color-success; }
  &.failed { color: $color-danger; }
  &.streaming { color: $color-primary; }
}

.rc-time {
  font-size: $font-size-xs;
  color: $text-hint;
  margin-left: auto;
}

// Mobile
@media (max-width: 768px) {
  .planning-page {
    flex-direction: column;
    height: auto;
    gap: 12px;
  }

  .input-panel {
    width: 100%;
    border-radius: 0;
    box-shadow: none;
  }

  .output-panel {
    min-height: 60vh;
    border-radius: 0;
    box-shadow: none;
    border-top: 0.5px solid $border-light;
  }

  .recent-grid { grid-template-columns: 1fr; }
}
</style>
