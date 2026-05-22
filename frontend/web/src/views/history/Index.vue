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

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Empty -->
    <div v-else-if="!records.length" class="empty-state">
      <div class="empty-icon">📋</div>
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

    <!-- Pagination -->
    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination
        :current-page="page"
        :total="total"
        :page-size="pageSize"
        layout="prev, pager, next"
        @current-change="fetchRecords"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import { Van, Guide, User, Bicycle, Connection } from '@element-plus/icons-vue'
import { planningApi } from '@/api/planning'
import { useLoading } from '@/composables/useLoading'
import dayjs from 'dayjs'

const { loading, withLoading } = useLoading()
const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const activeFilter = ref('all')

const filters = [
  { label: '全部', value: 'all' },
  { label: '已完成', value: 'completed' },
  { label: '生成中', value: 'streaming' },
  { label: '失败', value: 'failed' },
]

const statusMap = { pending: '等待中', streaming: '生成中', completed: '已完成', failed: '失败', canceled: '已取消' }
const transportMap = { driving: '自驾', transit: '公交', walking: '步行', cycling: '骑行', mixed: '混合' }
const transportIcons = { driving: Van, transit: Guide, walking: User, cycling: Bicycle, mixed: Connection }

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
  activeFilter.value = value
  page.value = 1
  fetchRecords()
}

const fetchRecords = withLoading(async () => {
  const params = { page: page.value, page_size: pageSize }
  if (activeFilter.value !== 'all') params.status = activeFilter.value
  const res = await planningApi.getRecords(params)
  records.value = res.data?.items || []
  total.value = res.data?.total || 0
})

onMounted(() => fetchRecords())
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
  transition: all 0.2s;
  box-shadow: $shadow-sm;

  &.active {
    background: $text-primary;
    color: #fff;
    font-weight: 600;
  }

  &:hover:not(.active) {
    background: #f5f5f5;
    color: $text-primary;
  }
}

// Loading
.loading-state {
  text-align: center;
  padding: 80px 0;
  color: $text-secondary;
}

.loading-spinner {
  width: 36px; height: 36px;
  border: 3px solid $border-light;
  border-top-color: $color-primary;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin { to { transform: rotate(360deg); } }

// Empty
.empty-state {
  text-align: center;
  padding: 72px 24px;
}

.empty-icon { font-size: 52px; margin-bottom: 12px; }
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

// Pagination
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 28px;
}

// Mobile
@media (max-width: 768px) {
  .history-page {
    padding: 0 4px;
  }

  .page-title { font-size: 22px; }

  .filter-tabs {
    overflow-x: auto;
    padding-bottom: 4px;
    -webkit-overflow-scrolling: touch;
    &::-webkit-scrollbar { display: none; }
  }

  .filter-btn {
    flex-shrink: 0;
    padding: 7px 16px;
    font-size: 12px;
  }

  .place-from, .place-to { max-width: 110px; }
}
</style>
