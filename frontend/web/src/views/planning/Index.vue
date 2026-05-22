<template>
  <div class="planning-page">
    <section class="planning-hero">
      <div class="hero-copy">
        <h1>今天想去哪儿？</h1>
        <p>填几个关键信息，生成一份可执行的出行规划。</p>
      </div>
      <div class="hero-rail" aria-label="规划能力">
        <span><el-icon><Cloudy /></el-icon>天气</span>
        <span><el-icon><MapLocation /></el-icon>路线</span>
      </div>
    </section>

    <div class="planning-workspace" :class="{ 'has-output': shouldShowOutputPanel }">
      <!-- Input Panel - Step Wizard -->
      <aside v-if="!shouldShowOutputPanel" class="input-panel">
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
            <span class="dot-circle">
              <el-icon v-if="i < currentStep"><Check /></el-icon>
              <span v-else>{{ i + 1 }}</span>
            </span>
            <span class="dot-label">{{ s.label }}</span>
          </button>
        </div>

        <!-- Step Content -->
        <div class="step-body" :key="currentStep">
          <transition name="step-fade" mode="out-in">
            <!-- Step 0: Where -->
            <div v-if="currentStep === 0" key="where" class="step-content">
              <div class="step-mark">
                <el-icon><Location /></el-icon>
              </div>
              <h3 class="step-title">去哪儿？</h3>
              <p class="step-desc">输入起点、目的地和这次出行的范围。</p>
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
              <div class="step-mark">
                <el-icon><Van /></el-icon>
              </div>
              <h3 class="step-title">怎么去？</h3>
              <p class="step-desc">选择适合这次计划的主要交通方式。</p>
              <div class="transport-grid">
                <button
                  v-for="opt in transportOptions"
                  :key="opt.value"
                  type="button"
                  class="transport-option"
                  :class="{ active: form.transport_mode === opt.value }"
                  @click="form.transport_mode = opt.value"
                >
                  <component :is="opt.icon" class="t-icon" />
                  <span class="t-copy">
                    <span class="t-label">{{ opt.label }}</span>
                    <span class="t-desc">{{ opt.desc }}</span>
                  </span>
                  <span class="option-check"><el-icon><Check /></el-icon></span>
                </button>
              </div>
            </div>

            <!-- Step 2: When & People -->
            <div v-else-if="currentStep === 2" key="when" class="step-content">
              <div class="step-mark">
                <el-icon><Calendar /></el-icon>
              </div>
              <h3 class="step-title">什么时候？</h3>
              <p class="step-desc">日期和人数会影响节奏、排队和餐饮建议。</p>
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
                    <button type="button" class="people-btn" @click="form.people_count > 1 && form.people_count--">
                      <el-icon><Minus /></el-icon>
                    </button>
                    <span class="people-num">{{ form.people_count }}</span>
                    <button type="button" class="people-btn" @click="form.people_count < 20 && form.people_count++">
                      <el-icon><Plus /></el-icon>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 3: Preferences -->
            <div v-else-if="currentStep === 3" key="pref" class="step-content">
              <div class="step-mark">
                <el-icon><Star /></el-icon>
              </div>
              <h3 class="step-title">偏好与避开</h3>
              <p class="step-desc">让计划更贴近你的出行习惯。</p>
              <div class="step-form">
                <div class="input-group">
                  <label class="input-label">偏好</label>
                  <div class="tag-grid">
                    <button
                      v-for="p in preferenceOptions"
                      :key="p"
                      type="button"
                      class="tag-item"
                      :class="{ active: form.preferences.includes(p) }"
                      @click="togglePreference(p)"
                    >{{ p }}</button>
                  </div>
                </div>
                <div class="input-group">
                  <label class="input-label">避开</label>
                  <div class="tag-grid">
                    <button
                      v-for="a in avoidanceOptions"
                      :key="a"
                      type="button"
                      class="tag-item avoid-tag"
                      :class="{ active: form.avoidances.includes(a) }"
                      @click="toggleAvoidance(a)"
                    >{{ a }}</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 4: Confirm -->
            <div v-else-if="currentStep === 4" key="confirm" class="step-content">
              <div class="step-mark">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <h3 class="step-title">确认信息</h3>
              <p class="step-desc">生成前再看一眼关键条件。</p>
              <div class="confirm-cards">
                <div class="confirm-item">
                  <span class="ci-label"><el-icon><Location /></el-icon> 去哪儿</span>
                  <span class="ci-val">{{ form.origin }} → {{ form.destination }}</span>
                  <span class="ci-sub">{{ form.range }}</span>
                </div>
                <div class="confirm-item">
                  <span class="ci-label"><el-icon><Guide /></el-icon> 怎么去</span>
                  <span class="ci-val">{{ transportOptions.find(o => o.value === form.transport_mode)?.label }}</span>
                </div>
                <div class="confirm-item" v-if="form.travel_date || form.people_count > 1">
                  <span class="ci-label"><el-icon><Calendar /></el-icon> 出行信息</span>
                  <span class="ci-val">
                    {{ form.travel_date ? form.travel_date + ' · ' : '' }}{{ form.people_count }}人
                  </span>
                </div>
                <div class="confirm-item" v-if="form.preferences.length">
                  <span class="ci-label"><el-icon><Star /></el-icon> 偏好</span>
                  <span class="ci-val">{{ form.preferences.join('、') }}</span>
                </div>
                <div class="confirm-item" v-if="form.avoidances.length">
                  <span class="ci-label"><el-icon><CircleClose /></el-icon> 避开</span>
                  <span class="ci-val">{{ form.avoidances.join('、') }}</span>
                </div>
              </div>

              <div v-if="outputState?.status === 'failed' && streamErrorMessage" class="confirm-error">
                <el-icon><Warning /></el-icon>
                <span>{{ streamErrorMessage }}</span>
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
                <span v-else>开始生成</span>
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
            上一步
          </button>
          <div v-else class="nav-spacer"></div>
          <button class="nav-btn next" @click="handleNext">
            {{ currentStep === 3 ? '确认信息' : '下一步' }}
            <el-icon><ArrowRight /></el-icon>
          </button>
        </div>
      </aside>

      <!-- Output Panel -->
      <section v-if="shouldShowOutputPanel" class="output-panel" ref="outputPanel">
        <div class="stream-status-bar">
          <div class="status-left">
            <span class="status-dot" :class="streaming ? 'streaming' : outputState?.status"></span>
            <span class="status-text">{{ statusLabel || '规划输出' }}</span>
            <span v-if="currentStageName" class="stage-badge">{{ currentStageName }}</span>
            <span v-if="duration" class="duration">{{ duration }}</span>
          </div>
          <div class="status-right">
            <button v-if="streaming" class="action-btn stop" @click="handleCancel">停止生成</button>
            <button v-if="!streaming && outputState?.status === 'completed'" class="action-btn copy" @click="copyResult">
              <el-icon><CopyDocument /></el-icon>复制结果
            </button>
          </div>
        </div>

        <template v-if="streaming || outputState">
          <div class="stage-steps" v-if="stages.length">
            <div v-for="s in stages" :key="s.key" class="step-item" :class="{ active: s.active, done: s.done }">
              <span class="step-dot"></span>
              <span class="step-label">{{ s.label }}</span>
            </div>
          </div>

          <div class="stream-content" ref="streamContent" @scroll.passive="handleStreamScroll">
            <div v-if="streamErrorMessage" class="content-card" :class="streamMessageCardClass">
              <div class="card-label"><el-icon><Warning /></el-icon>{{ streamMessageTitle }}</div>
              <p>{{ streamErrorMessage }}</p>
            </div>
            <div v-if="weatherSummary" class="content-card weather-card">
              <div class="card-label"><el-icon><Cloudy /></el-icon>天气预警</div>
              <p>{{ weatherSummary }}</p>
              <div v-if="weatherMeta" class="source-meta">{{ weatherMeta }}</div>
            </div>
            <div v-if="routeSummary" class="content-card route-card">
              <div class="card-label"><el-icon><MapLocation /></el-icon>路线建议</div>
              <p>{{ routeSummary }}</p>
            </div>
            <div v-if="transportSummary" class="content-card transport-card">
              <div class="card-label"><el-icon><Guide /></el-icon>交通建议</div>
              <p>{{ transportSummary }}</p>
            </div>
            <div v-if="amapUrl || routeMapImage" class="content-card map-card">
              <div class="card-label"><el-icon><Location /></el-icon>高德路线图</div>
              <img
                v-if="routeMapImage"
                :src="routeMapImage"
                class="route-map-img"
                alt="路线图"
                @load="scrollOutputToBottom"
              />
              <div v-if="navigationWaypointItems.length" class="waypoint-strip">
                <span class="waypoint-title">途径</span>
                <span
                  v-for="(item, index) in navigationWaypointItems"
                  :key="`${item.location || item.name}-${index}`"
                  class="waypoint-chip"
                  :title="waypointTitle(item)"
                >
                  <span class="waypoint-name">{{ item.name || item.location }}</span>
                  <span v-if="waypointSourceLabel(item.source)" class="waypoint-source">
                    {{ waypointSourceLabel(item.source) }}
                  </span>
                </span>
              </div>
              <div v-if="mapMeta" class="source-meta">{{ mapMeta }}</div>
              <div class="map-actions">
                <a v-if="amapUrl" :href="amapUrl" target="_blank" class="amap-link">打开高德路线</a>
                <button v-if="routeMapImage" class="download-btn" @click.stop="downloadRouteMap">
                  <el-icon><Download /></el-icon>保存路线图
                </button>
              </div>
            </div>
            <div v-if="attractionsSummary" class="content-card attr-card">
              <div class="card-label"><el-icon><Place /></el-icon>途径景点</div>
              <p>{{ attractionsSummary }}</p>
            </div>
            <div v-if="realtimeSummary" class="content-card realtime-card">
              <div class="card-label"><el-icon><DataLine /></el-icon>实时信息</div>
              <div class="realtime-markdown" v-html="renderedRealtimeSummary"></div>
              <div v-if="realtimeMeta" class="source-meta">{{ realtimeMeta }}</div>
            </div>
            <div v-if="streamTokens" class="stream-tokens" v-html="renderedTokens"></div>
            <div v-if="finalMarkdown" class="final-markdown" v-html="renderedMarkdown"></div>
            <span v-if="streaming" class="cursor-blink">|</span>
          </div>
        </template>
        <div v-else class="output-empty">
          <div class="empty-visual">
            <el-icon><Compass /></el-icon>
          </div>
          <p class="empty-title">你的规划会在这里展开</p>
          <p class="empty-desc">从天气、路线、交通、景点到实时信息，生成过程会按阶段呈现。</p>
          <div class="empty-features">
            <span class="feat-item"><el-icon><Cloudy /></el-icon>天气预警</span>
            <span class="feat-item"><el-icon><MapLocation /></el-icon>路线规划</span>
            <span class="feat-item"><el-icon><Place /></el-icon>景点推荐</span>
            <span class="feat-item"><el-icon><DataLine /></el-icon>实时资讯</span>
          </div>
        </div>
      </section>
    </div>

    <!-- Recent history records below output -->
    <div v-if="recentRecords.length && !streaming" class="recent-records">
      <div class="recent-header">
        <h4>最近的规划记录</h4>
        <button class="view-all-link" @click="$router.push('/history')">查看全部</button>
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
import {
  ArrowRight,
  Bicycle,
  Calendar,
  Check,
  CircleCheck,
  CircleClose,
  Cloudy,
  Compass,
  Connection,
  CopyDocument,
  DataLine,
  Download,
  Guide,
  Location,
  MapLocation,
  Minus,
  Place,
  Plus,
  Star,
  User,
  Van,
  Warning,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { planningApi } from '@/api/planning'
import { createStreamClient } from '@/utils/stream'
import { marked } from 'marked'

import dayjs from 'dayjs'

const auth = useAuthStore()
const outputPanel = ref(null)
const streamContent = ref(null)
const autoScrollOutput = ref(true)
const outputBottomThreshold = 48
let scrollFrameId = 0

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
  { value: 'transit', label: '公共交通', desc: '地铁公交', icon: Guide },
  { value: 'walking', label: '步行', desc: '慢行探索', icon: User },
  { value: 'cycling', label: '骑行', desc: '健康环保', icon: Bicycle },
  { value: 'motorcycle', label: '摩托车', desc: '两轮出行', icon: Compass },
  { value: 'mixed', label: '混合出行', desc: '智能搭配', icon: Connection },
]

const preferenceOptions = ['自然风光', '人文历史', '亲子友好', '美食探店', '小众路线', '低强度', '咖啡']
const avoidanceOptions = ['不走高速', '少换乘', '少步行', '避开热门', '避开收费']

const statusMap = { pending: '等待中', streaming: '生成中', completed: '已完成', failed: '失败', canceled: '已取消' }
const transportMap = { driving: '自驾', transit: '公共交通', walking: '步行', cycling: '骑行', motorcycle: '摩托车', mixed: '混合出行' }
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
const navigationWaypointItems = ref([])
const mapSource = ref(null)
const attractionsSummary = ref('')
const realtimeSummary = ref('')
const realtimeSource = ref(null)
const finalMarkdown = ref('')
const streamErrorMessage = ref('')
const streamRecoverableWarning = ref(false)
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
const streamMessageTitle = computed(() => (
  streamRecoverableWarning.value ? '阶段已降级' : '生成失败'
))
const streamMessageCardClass = computed(() => (
  streamRecoverableWarning.value ? 'warning-card' : 'error-card'
))

const renderedTokens = computed(() => marked.parse(streamTokens.value))
const renderedMarkdown = computed(() => finalMarkdown.value ? marked.parse(finalMarkdown.value) : '')
const renderedRealtimeSummary = computed(() => (
  realtimeSummary.value ? marked.parse(realtimeSummary.value) : ''
))
const weatherMeta = computed(() => formatSourceMeta(weatherSource.value))
const mapMeta = computed(() => formatSourceMeta(mapSource.value))
const realtimeMeta = computed(() => formatSourceMeta(realtimeSource.value))
const shouldShowOutputPanel = computed(() => streaming.value || outputState.value?.status === 'completed')

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

function normalizeWaypointItems(...sources) {
  const items = []
  const seen = new Set()
  for (const source of sources) {
    if (!source) continue
    const namedItems = source.navigation_waypoint_items || source.recommended_waypoint_items || []
    for (const item of namedItems) {
      if (!item || typeof item !== 'object') continue
      const key = item.location || item.name
      if (!key || seen.has(key)) continue
      seen.add(key)
      items.push({
        name: item.name || item.location || '途径点',
        location: item.location || '',
        source: item.source || '',
        reason: item.reason || '',
        source_title: item.source_title || '',
        source_url: item.source_url || '',
      })
    }
    const locations = source.navigation_waypoints || source.requested_waypoints || []
    for (const location of locations) {
      if (!location || seen.has(location)) continue
      seen.add(location)
      items.push({ name: location, location, source: '', reason: '' })
    }
  }
  return items.slice(0, 5)
}

function waypointSourceLabel(source) {
  if (source === 'web_search') return '全网'
  if (source === 'amap_poi') return '高德'
  return ''
}

function waypointTitle(item) {
  const parts = [item.name, item.reason, item.source_title, item.source_url].filter(Boolean)
  return parts.join(' · ')
}

function failGeneration(message, data = {}) {
  streaming.value = false
  streamRecoverableWarning.value = false
  streamErrorMessage.value = message || '生成失败'
  outputState.value = { status: 'failed' }
  if (data.duration_ms) duration.value = `${(data.duration_ms / 1000).toFixed(1)}s`
  stages.forEach(s => { s.active = false })
  ElMessage.error(streamErrorMessage.value)
}

function handleStreamError(data) {
  if (data?.error_code === 'LLM_STAGE_FAILED') {
    streamRecoverableWarning.value = true
    streamErrorMessage.value = data.message || '当前阶段大模型输出中断，已降级继续生成。'
    ElMessage.warning(streamErrorMessage.value)
    return
  }
  failGeneration(data?.message || '生成失败', data)
}

async function handleGenerate() {
  if (!auth.isAuthenticated) await auth.initGuestSession()

  resetOutput()
  streaming.value = true
  scrollOutputToBottom(true)

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
        scrollOutputToBottom()
      },
      onToken(data) {
        streamTokens.value += data.content
        scrollOutputToBottom()
      },
      onSnapshot(data) {
        if (data.type === 'weather') {
          weatherSummary.value = data.data?.weather_summary || data.data?.summary || ''
          weatherSource.value = buildSourceMeta(data.data)
        }
        else if (data.type === 'route') {
          routeSummary.value = data.data?.route_summary || ''
          navigationWaypointItems.value = normalizeWaypointItems(data.data)
        }
        else if (data.type === 'transport') transportSummary.value = data.data?.transport_summary || ''
        else if (data.type === 'map_export') {
          amapUrl.value = data.data?.amap_route_url || ''
          routeMapImage.value = data.data?.image_url || data.data?.route_map_image || ''
          navigationWaypointItems.value = normalizeWaypointItems(data.data)
          mapSource.value = buildSourceMeta(data.data)
        }
        else if (data.type === 'attractions') attractionsSummary.value = data.data?.attractions_summary || ''
        else if (data.type === 'realtime') {
          realtimeSummary.value = data.data?.realtime_info_summary || ''
          realtimeSource.value = buildSourceMeta(data.data)
        }
        else if (data.type === 'summary') finalMarkdown.value = data.data?.final_markdown || ''
        scrollOutputToBottom()
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
        scrollOutputToBottom()
      },
      onError(data) {
        handleStreamError(data)
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
    const resultJson = output?.result_json || {}
    navigationWaypointItems.value = normalizeWaypointItems(
      resultJson.map_export,
      resultJson.route,
      res.data?.snapshots?.routes?.[0],
    )
    const mapExport = res.data?.snapshots?.map_exports?.[0]
    if (mapExport) {
      amapUrl.value = amapUrl.value || mapExport.amap_route_url || ''
      routeMapImage.value = mapExport.image_url || routeMapImage.value
      mapSource.value = buildSourceMeta(mapExport)
      if (!navigationWaypointItems.value.length) {
        navigationWaypointItems.value = normalizeWaypointItems(mapExport)
      }
    }
    const realtimeSnapshots = res.data?.snapshots?.realtime_info || {}
    const realtimeItems = [
      ...(realtimeSnapshots.news_traffic || []),
      ...(realtimeSnapshots.guide_pitfall || []),
    ]
    if (realtimeItems.length) realtimeSource.value = buildSourceMeta(realtimeItems[0])
    scrollOutputToBottom()
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
  navigationWaypointItems.value = []
  mapSource.value = null
  attractionsSummary.value = ''
  realtimeSummary.value = ''
  realtimeSource.value = null
  finalMarkdown.value = ''
  streamErrorMessage.value = ''
  streamRecoverableWarning.value = false
  duration.value = ''
  recordId.value = null
  outputState.value = null
  autoScrollOutput.value = true
  stages.forEach(s => { s.active = false; s.done = false })
}

function isOutputAtBottom() {
  const el = streamContent.value
  if (!el) return true
  return el.scrollHeight - el.scrollTop - el.clientHeight <= outputBottomThreshold
}

function handleStreamScroll() {
  autoScrollOutput.value = isOutputAtBottom()
}

function scrollOutputToBottom(force = false) {
  nextTick(() => {
    if (scrollFrameId) cancelAnimationFrame(scrollFrameId)
    scrollFrameId = requestAnimationFrame(() => {
      scrollFrameId = 0
      const el = streamContent.value
      if (!el) return
      if (force || autoScrollOutput.value || isOutputAtBottom()) {
        el.scrollTop = el.scrollHeight
        autoScrollOutput.value = true
      }
    })
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
  flex-direction: column;
  gap: 24px;
  min-height: calc(100vh - $nav-height - 40px);
}

.planning-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: rgba($content-bg, 0.7);
  border: 1px solid rgba($border-light, 0.88);
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
}

.hero-copy {
  display: flex;
  align-items: baseline;
  gap: 12px;
  min-width: 0;

  h1 {
    flex: 0 0 auto;
    font-size: 20px;
    font-weight: 750;
    letter-spacing: 0;
    line-height: 1.25;
    color: $text-primary;
    text-wrap: pretty;
  }

  p {
    min-width: 0;
    color: $text-secondary;
    font-size: $font-size-sm;
    line-height: 1.45;
    text-wrap: pretty;
  }
}

.hero-rail {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;

  span {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    min-height: 28px;
    padding: 5px 10px;
    color: $text-secondary;
    font-size: $font-size-xs;
    font-weight: 600;
    background: rgba($surface-soft, 0.8);
    border: 1px solid $border-light;
    border-radius: 999px;
  }

  .el-icon {
    color: $color-primary;
    font-size: 15px;
  }
}

.planning-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: stretch;
  min-height: 620px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba($surface-soft, 0.66), rgba($content-bg, 0.96)),
    $content-bg;
  border: 1px solid rgba($border-light, 0.9);
  border-radius: $radius-xl;
  box-shadow: $shadow-card;

  &.has-output {
    grid-template-columns: minmax(0, 1fr);
    height: max(620px, calc(100vh - $nav-height - 180px));
    min-height: 0;
    background:
      linear-gradient(180deg, rgba($surface-soft, 0.5), rgba($content-bg, 0.96)),
      $content-bg;

    .output-panel {
      border-left: 0;
    }
  }

  &:not(.has-output) {
    .input-panel {
      width: min(100%, 620px);
      justify-self: center;
    }
  }
}

// INPUT PANEL
.input-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  max-height: calc(100vh - $nav-height - 142px);
  overflow: hidden;
  background: transparent;
}

// Step Indicator
.step-indicator {
  display: flex;
  justify-content: center;
  gap: 0;
  padding: 20px 16px 12px;
  border-bottom: 1px solid rgba($border-card, 0.76);
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

.step-mark {
  display: grid;
  width: 50px;
  height: 50px;
  place-items: center;
  margin: 2px auto 12px;
  color: $color-primary;
  background: $color-primary-bg;
  border-radius: 18px;

  :deep(svg) {
    width: 26px;
    height: 26px;
  }
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

.transport-option {
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

  .t-copy {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .t-label {
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
  }

  .t-desc {
    font-size: $font-size-xs;
    color: $text-hint;
  }

  .option-check {
    display: grid;
    width: 22px;
    height: 22px;
    flex: 0 0 auto;
    place-items: center;
    color: transparent;
    border: 1px solid $border-light;
    border-radius: 999px;
  }

  &.active {
    border-color: $color-primary;
    background: $color-primary-bg;

    .t-icon { color: $color-primary; }
    .t-desc { color: $color-primary; }
    .option-check {
      color: #fff;
      background: $color-primary;
      border-color: $color-primary;
    }
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

.confirm-error {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 6px 0 14px;
  padding: 10px 12px;
  color: $color-danger;
  font-size: $font-size-sm;
  line-height: 1.5;
  background: rgba($color-danger, 0.07);
  border: 1px solid rgba($color-danger, 0.18);
  border-radius: $radius-sm;

  .el-icon {
    flex: 0 0 auto;
    margin-top: 2px;
  }
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

// OUTPUT PANEL
.output-panel {
  min-width: 0;
  min-height: 0;
  background: rgba($surface-soft, 0.58);
  border-left: 1px solid rgba($border-card, 0.82);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-height: 100%;
}

.stream-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: rgba($content-bg, 0.72);
  border-bottom: 1px solid rgba($border-card, 0.72);
  flex-shrink: 0;
  backdrop-filter: blur(12px);
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
  display: flex; flex-wrap: wrap; gap: 4px; padding: 10px 20px; border-bottom: 1px solid rgba($border-card, 0.72);
  flex-shrink: 0;
  background: rgba($content-bg, 0.52);
}

.step-item {
  display: flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 12px;
  font-size: $font-size-xs; color: $text-hint; white-space: nowrap; transition: all 0.2s;
  .step-dot { width: 6px; height: 6px; border-radius: 50%; background: $border-light; transition: all 0.2s; }
  &.active { color: $color-primary; font-weight: 600; background: $color-primary-bg; .step-dot { background: $color-primary; } }
  &.done { color: $color-success; .step-dot { background: $color-success; } }
}

.stream-content {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 20px 24px;
  color: $text-primary;
  font-size: $font-size-body;
  line-height: 1.8;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.content-card {
  min-width: 0;
  margin-bottom: 14px;
  padding: 16px 18px;
  background: rgba($content-bg, 0.84);
  border: 1px solid rgba($border-card, 0.82);
  border-radius: $radius-md;
  overflow-wrap: anywhere;
  word-break: break-word;

  .card-label {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: $font-size-sm;
    font-weight: 600;
    color: $text-secondary;
    margin-bottom: 8px;

    .el-icon {
      color: $color-primary;
      font-size: 16px;
    }
  }

  p {
    font-size: $font-size-body;
    line-height: 1.7;
    overflow-wrap: anywhere;
    word-break: break-word;
  }

  &.error-card {
    background: rgba($color-danger, 0.06);
    border: 1px solid rgba($color-danger, 0.18);

    .card-label,
    p {
      color: $color-danger;
    }
  }

  &.warning-card {
    background: rgba($color-warning, 0.08);
    border: 1px solid rgba($color-warning, 0.22);

    .card-label,
    p {
      color: $color-warning;
    }
  }
}

.map-card .amap-link {
  color: $color-link;
  font-weight: 500;
  overflow-wrap: anywhere;
  word-break: break-word;

  &:hover { text-decoration: underline; }
}

.source-meta {
  margin-top: 8px;
  font-size: $font-size-xs;
  color: $text-hint;
  line-height: 1.5;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.route-map-img {
  width: 100%;
  border-radius: $radius-sm;
  margin-bottom: 10px;
  border: 1px solid $border-light;
}

.waypoint-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: 0 0 10px;
}

.waypoint-title {
  font-size: $font-size-xs;
  font-weight: 600;
  color: $text-hint;
}

.waypoint-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  min-height: 26px;
  padding: 4px 9px;
  color: $text-secondary;
  font-size: $font-size-xs;
  line-height: 1.35;
  background: $page-bg;
  border: 1px solid $border-light;
  border-radius: 999px;
}

.waypoint-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.waypoint-source {
  flex: 0 0 auto;
  color: $color-primary;
  font-weight: 600;
}

.map-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.download-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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

.final-markdown, .stream-tokens, .realtime-markdown {
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;

  :deep(h2) { font-size: 18px; margin: 20px 0 10px; }
  :deep(h3) { font-size: 16px; margin: 16px 0 8px; }
  :deep(p) {
    margin-bottom: 10px;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
  :deep(ul), :deep(ol) { padding-left: 20px; margin-bottom: 10px; }
  :deep(li) {
    margin-bottom: 4px;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
  :deep(a),
  :deep(code),
  :deep(pre) {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
}

.cursor-blink { animation: blink 1s infinite; color: $color-primary; font-weight: 300; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

// Empty state
.output-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px 32px; text-align: center;
  background:
    linear-gradient(180deg, rgba($content-bg, 0.58), rgba($surface-soft, 0.38));
}
.empty-visual {
  display: grid;
  width: 68px;
  height: 68px;
  place-items: center;
  margin-bottom: 16px;
  color: #fff;
  background: $color-ink;
  border-radius: 24px;
  box-shadow: $shadow-md;

  :deep(svg) {
    width: 34px;
    height: 34px;
  }
}
.empty-title { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.empty-desc { font-size: $font-size-sm; color: $text-secondary; line-height: 1.6; margin-bottom: 24px; }
.empty-features { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.feat-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: $font-size-sm;
  padding: 6px 14px;
  background: $page-bg;
  border-radius: 20px;
  color: $text-secondary;

  .el-icon {
    color: $color-primary;
  }
}

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
    height: auto;
    gap: 12px;
  }

  .planning-hero {
    grid-template-columns: 1fr;
    gap: 10px;
    padding: 12px 14px;
  }

  .hero-copy {
    display: block;

    h1 {
      font-size: 18px;
    }

    p {
      margin-top: 4px;
    }
  }

  .hero-rail {
    justify-content: flex-start;
  }

  .planning-workspace {
    display: flex;
    flex-direction: column;
    min-height: auto;
    gap: 0;
    border-radius: $radius-lg;

    &.has-output {
      height: calc(100dvh - $tab-height - 112px);
      min-height: 420px;
    }
  }

  .input-panel {
    width: 100%;
    max-height: none;
  }

  .output-panel {
    min-height: 0;
    flex: 1;
    border-top: 1px solid rgba($border-card, 0.86);
    border-left: 0;
  }

  .recent-grid { grid-template-columns: 1fr; }
}
</style>
