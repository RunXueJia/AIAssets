<template>
  <div class="history-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-top">
        <div>
          <h2 class="page-title">我的规划</h2>
          <p class="page-sub">共 {{ total }} 条记录</p>
        </div>
      </div>

      <!-- Filter tabs -->
      <div class="filter-tabs">
        <button
          v-for="f in filters"
          :key="f.value"
          class="filter-btn"
          :class="{ active: activeFilter === f.value }"
          @click="switchFilter(f.value)"
        >
          {{ f.label }}
        </button>
      </div>
    </div>

    <div ref="scrollAreaRef" class="history-scroll-area" @scroll="handleScroll">
      <!-- Loading -->
      <div v-if="loading && !records.length" class="loading-state">
        <div class="loading-orb" aria-hidden="true">
          <span></span>
        </div>
        <p>加载中...</p>
        <div class="loading-skeleton-list" aria-hidden="true">
          <div v-for="i in 3" :key="i" class="loading-skeleton-card">
            <span class="skeleton-icon"></span>
            <span class="skeleton-lines">
              <span></span>
              <span></span>
            </span>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="!records.length" class="empty-state">
        <div class="empty-icon">
          <el-icon><Tickets /></el-icon>
        </div>
        <p class="empty-title">
          {{ activeFilter === 'all' ? '还没有生成记录' : statusLabel(activeFilter) + '的记录暂无' }}
        </p>
        <p class="empty-desc" v-if="activeFilter === 'all'">去首页创建你的第一条出行规划吧</p>
        <el-button v-if="activeFilter === 'all'" type="primary" round @click="$router.push('/')">去规划</el-button>
      </div>

      <!-- Record List -->
      <div v-else class="record-list">
        <div
          v-for="item in records"
          :key="item.id"
          class="record-card"
          :class="'card-' + item.status"
          @click="$router.push(`/history/${item.id}`)"
        >
          <!-- Left accent bar -->
          <div class="card-accent" :class="item.status"></div>

          <div class="card-body">
            <!-- Top row: transport icon + route + status -->
            <div class="card-main">
              <div class="transport-icon" :class="item.transport_mode">
                <component :is="transportIcon(item.transport_mode)" />
              </div>
              <div class="route-info">
                <div class="route-line">
                  <span class="place-from">{{ item.origin_text }}</span>
                  <span class="route-arrow">→</span>
                  <span class="place-to">{{ item.destination_text }}</span>
                </div>
                <div class="route-meta">
                  <span class="meta-tag">{{ transportLabel(item.transport_mode) }}</span>
                  <span v-if="item.summary_title" class="meta-summary">{{ item.summary_title }}</span>
                </div>
              </div>
              <span class="status-dot-mini" :class="item.status"></span>
            </div>

            <!-- Bottom row: time + actions -->
            <div class="card-foot">
              <span class="record-time">{{ formatRelative(item.created_at) }}</span>
              <span class="record-date">{{ formatDate(item.created_at) }}</span>
              <span v-if="item.duration_ms" class="record-duration">耗时 {{ (item.duration_ms / 1000).toFixed(0) }}s</span>
            </div>
          </div>

          <div class="card-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <div v-if="records.length" class="load-more-state">
        <template v-if="loadingMore">
          <span class="load-more-dot"></span>
          <span>正在加载...</span>
        </template>
        <template v-else-if="hasMore">
          <span>继续下滑加载更多</span>
        </template>
        <template v-else>
          <span>已加载全部</span>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowRight, Tickets } from '@element-plus/icons-vue'
import { Van, Guide, User, Bicycle, Compass, Connection } from '@element-plus/icons-vue'
import { planningApi } from '@/api/planning'
import dayjs from 'dayjs'

const loading = ref(false)
const loadingMore = ref(false)
const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const activeFilter = ref('all')
const scrollAreaRef = ref(null)
let scrollCheckTimer = null

const filters = [
  { label: '全部', value: 'all' },
  { label: '已完成', value: 'completed' },
  { label: '生成中', value: 'streaming' },
  { label: '失败', value: 'failed' },
]

const statusMap = { pending: '等待中', streaming: '生成中', completed: '已完成', failed: '失败', canceled: '已取消' }
const transportMap = { driving: '自驾', transit: '公共交通', walking: '步行', cycling: '骑行', motorcycle: '摩托车', mixed: '混合出行' }
const transportIcons = { driving: Van, transit: Guide, walking: User, cycling: Bicycle, motorcycle: Compass, mixed: Connection }
const hasMore = computed(() => records.value.length < total.value)

function statusLabel(s) { return statusMap[s] || s }
function transportLabel(t) { return transportMap[t] || t }
function transportIcon(t) { return transportIcons[t] || Connection }

function formatDate(t) {
  if (!t) return ''
  const d = dayjs(t)
  const now = dayjs()
  if (d.isSame(now, 'day')) return '今天 ' + d.format('HH:mm')
  if (d.isSame(now.subtract(1, 'day'), 'day')) return '昨天 ' + d.format('HH:mm')
  return d.format('MM-DD HH:mm')
}

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

function switchFilter(value) {
  if (activeFilter.value === value) return
  activeFilter.value = value
  fetchRecords({ reset: true })
}

async function fetchRecords({ reset = false } = {}) {
  if (loading.value || loadingMore.value) return
  if (!reset && records.value.length && !hasMore.value) return

  if (reset) {
    records.value = []
    total.value = 0
    page.value = 0
    await nextTick()
    if (scrollAreaRef.value) scrollAreaRef.value.scrollTop = 0
  }

  const nextPage = reset ? 1 : page.value + 1
  loading.value = reset || !records.value.length
  loadingMore.value = !loading.value
  let loaded = false

  try {
    const params = { page: nextPage, page_size: pageSize }
    if (activeFilter.value !== 'all') params.status = activeFilter.value
    const res = await planningApi.getRecords(params)
    const nextItems = res.data?.items || []
    total.value = res.data?.total || 0
    page.value = nextPage
    records.value = reset ? nextItems : records.value.concat(nextItems)
    if (!nextItems.length && records.value.length < total.value) {
      total.value = records.value.length
    }
    loaded = true
  } finally {
    loading.value = false
    loadingMore.value = false
  }

  if (loaded) {
    await nextTick()
    checkAndLoadMore()
  }
}

function handleScroll() {
  if (scrollCheckTimer) window.clearTimeout(scrollCheckTimer)
  scrollCheckTimer = window.setTimeout(checkAndLoadMore, 80)
}

function checkAndLoadMore() {
  const el = scrollAreaRef.value
  if (!el || loading.value || loadingMore.value || !hasMore.value) return
  const isInnerScroll = el.scrollHeight > el.clientHeight + 1
  const distanceToBottom = isInnerScroll
    ? el.scrollHeight - el.scrollTop - el.clientHeight
    : document.documentElement.scrollHeight - window.scrollY - window.innerHeight

  if (distanceToBottom <= 96) {
    fetchRecords()
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  fetchRecords({ reset: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  if (scrollCheckTimer) {
    window.clearTimeout(scrollCheckTimer)
    scrollCheckTimer = null
  }
})
</script>

<style lang="scss" scoped>
.history-page {
  max-width: 680px;
  margin: 0 auto;
}

// Header
.page-header {
  margin-bottom: 20px;
}

.header-top {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-title {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.page-sub {
  font-size: $font-size-sm;
  color: $text-hint;
  margin-top: 2px;
}

.history-scroll-area {
  min-height: 0;
}

// Filter tabs
.filter-tabs {
  display: flex;
  gap: 8px;
}

.filter-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 20px;
  background: $content-bg;
  color: $text-secondary;
  font-size: $font-size-sm;
  font-weight: 500;
  cursor: pointer;
  transition:
    color 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
  box-shadow: $shadow-sm;

  &.active {
    background: $content-bg;
    color: $text-primary;
    font-weight: 600;
    box-shadow:
      inset -5px -5px 10px rgba(255, 255, 255, 0.68),
      inset 5px 5px 10px rgba(163, 177, 198, 0.42);
  }

  &:hover:not(.active) {
    background: $content-bg;
    color: $text-primary;
    transform: translateY(-1px);
    box-shadow: $shadow-md;
  }
}

// Loading
.loading-state {
  text-align: center;
  padding: 56px 0 24px;
  color: $text-secondary;
}

.loading-orb {
  width: 54px;
  height: 54px;
  display: grid;
  place-items: center;
  margin: 0 auto 16px;
  border-radius: 50%;
  background: $content-bg;
  box-shadow: $shadow-md;

  span {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: $content-bg;
    box-shadow:
      inset -5px -5px 10px rgba(255, 255, 255, 0.68),
      inset 5px 5px 10px rgba(163, 177, 198, 0.42);
    animation: soft-pulse 1.05s ease-in-out infinite;
  }
}

.loading-state p {
  font-size: $font-size-sm;
  font-weight: 600;
}

.loading-skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 24px;
}

.loading-skeleton-card {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 80px;
  padding: 16px;
  border-radius: 16px;
  background: $content-bg;
  box-shadow: $shadow-sm;
}

.skeleton-icon,
.skeleton-lines span {
  display: block;
  border-radius: 999px;
  background: $content-bg;
  box-shadow:
    inset -4px -4px 8px rgba(255, 255, 255, 0.62),
    inset 4px 4px 8px rgba(163, 177, 198, 0.28);
}

.skeleton-icon {
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
}

.skeleton-lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;

  span:first-child {
    width: 72%;
    height: 14px;
  }

  span:last-child {
    width: 46%;
    height: 10px;
  }
}

@keyframes soft-pulse {
  0%, 100% {
    transform: scale(0.82);
    opacity: 0.74;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }
}

// Empty
.empty-state {
  text-align: center;
  padding: 72px 24px;
}

.empty-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  margin-bottom: 12px;
  color: $color-primary;
  background: $color-primary-bg;
  border-radius: 20px;

  :deep(svg) {
    width: 30px;
    height: 30px;
  }
}
.empty-title { font-size: 16px; font-weight: 600; color: $text-primary; margin-bottom: 6px; }
.empty-desc { font-size: $font-size-sm; color: $text-secondary; margin-bottom: 20px; }

// Record list
.record-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.record-card {
  display: flex;
  align-items: stretch;
  background: $content-bg;
  border-radius: $radius-lg;
  cursor: pointer;
  box-shadow: $shadow-card;
  transition: all 0.2s;
  overflow: hidden;
  min-height: 80px;

  &:hover {
    transform: translateY(-1px);
    box-shadow: $shadow-md;
  }

  &:active { transform: scale(0.99); }
}

// Left accent strip
.card-accent {
  width: 4px;
  flex-shrink: 0;
  border-radius: $radius-lg 0 0 $radius-lg;

  &.completed { background: $color-success; }
  &.streaming { background: $color-primary; animation: accent-pulse 1.5s infinite; }
  &.failed { background: $color-danger; }
  &.pending { background: $text-hint; }
  &.canceled { background: $border-light; }
}

@keyframes accent-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.card-body {
  flex: 1;
  padding: 16px 12px 16px 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
  min-width: 0;
}

// Main row
.card-main {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.transport-icon {
  width: 40px; height: 40px;
  border-radius: $radius-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: $text-secondary;
  margin-top: 2px;

  &.driving { background: rgba(#5856d6, 0.08); color: #5856d6; }
  &.transit { background: rgba(#ff9500, 0.08); color: #ff9500; }
  &.walking { background: rgba($color-success, 0.08); color: $color-success; }
  &.cycling { background: rgba(#007aff, 0.08); color: #007aff; }
  &.motorcycle { background: rgba(#8e5cf7, 0.08); color: #8e5cf7; }
  &.mixed { background: $color-primary-bg; color: $color-primary; }

  :deep(svg) { width: 20px; height: 20px; }
}

.route-info {
  flex: 1;
  min-width: 0;
}

.route-line {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 4px;
}

.place-from, .place-to {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}

.route-arrow {
  color: $text-hint;
  font-weight: 300;
  flex-shrink: 0;
}

.route-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-tag {
  font-size: $font-size-xs;
  padding: 2px 8px;
  border-radius: 6px;
  background: $page-bg;
  color: $text-secondary;
  flex-shrink: 0;
}

.meta-summary {
  font-size: $font-size-xs;
  color: $text-hint;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// Status dot mini
.status-dot-mini {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;

  &.completed { background: $color-success; }
  &.streaming { background: $color-primary; animation: pulse-dot 1.5s infinite; }
  &.failed { background: $color-danger; }
  &.pending { background: $text-hint; }
  &.canceled { background: $border-light; }
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(1.6); }
}

// Foot row
.card-foot {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 0;
}

.record-time {
  font-size: $font-size-xs;
  color: $text-hint;
  font-weight: 500;
}

.record-date {
  font-size: $font-size-xs;
  color: $border-light;

  &::before { content: '·'; margin-right: 6px; color: $border-light; }
}

.record-duration {
  font-size: $font-size-xs;
  color: $text-hint;
  margin-left: auto;
}

// Arrow
.card-arrow {
  display: flex;
  align-items: center;
  padding-right: 14px;
  color: $border-light;
  font-size: 16px;
  flex-shrink: 0;
}

.load-more-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  margin-top: 16px;
  color: $text-hint;
  font-size: $font-size-xs;
  font-weight: 600;
}

.load-more-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: $color-primary-dark;
  box-shadow:
    -3px -3px 6px rgba(255, 255, 255, 0.68),
    3px 3px 6px rgba(163, 177, 198, 0.38);
  animation: soft-pulse 1.05s ease-in-out infinite;
}

// Mobile
@media (max-width: 768px) {
  .history-page {
    height: calc(100dvh - 24px - #{$tab-height} - env(safe-area-inset-bottom, 0px) - 18px);
    min-height: 0;
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow: hidden;
  }

  .page-header {
    flex: 0 0 auto;
    margin-bottom: 8px;
    padding: 0 4px 2px;
    overflow: visible;
  }

  .header-top {
    margin-bottom: 8px;
  }

  .page-title {
    font-size: 22px;
  }

  .filter-tabs {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    overflow: visible;
    padding: 10px 8px 14px;
    margin: 0 -4px;
    &::-webkit-scrollbar { display: none; }
  }

  .filter-btn {
    min-width: 0;
    padding: 7px 10px;
    font-size: 12px;
  }

  .history-scroll-area {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    overscroll-behavior: contain;
    margin: 0 -8px;
    padding: 16px 16px 28px;
    -webkit-overflow-scrolling: touch;
  }

  .record-list {
    gap: 14px;
  }

  .record-card,
  .loading-skeleton-card {
    border-radius: 16px;
    box-shadow: $shadow-sm;
  }

  .record-card:hover {
    box-shadow: $shadow-md;
  }

  .loading-state {
    padding-top: 34px;
  }

  .loading-skeleton-list {
    margin-top: 20px;
  }

  .empty-state {
    min-height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 34px 24px;
  }

  .place-from, .place-to { max-width: 110px; }
}
</style>
