<template>
  <div class="detail-page" v-loading="loading">
    <template v-if="detail">
      <button class="back-link" @click="$router.push('/history')">
        <el-icon><ArrowLeft /></el-icon> 返回
      </button>

      <div class="detail-header">
        <h2>{{ detail.input?.origin_text || '' }} → {{ detail.input?.destination_text || '' }}</h2>
        <div class="detail-tags">
          <span class="status-badge" :class="detail.record?.status">{{ statusLabel(detail.record?.status) }}</span>
          <span class="info-tag">{{ transportLabel(detail.record?.transport_mode) }}</span>
          <span class="info-tag" v-if="detail.record?.duration_ms">{{ (detail.record.duration_ms / 1000).toFixed(1) }}s</span>
          <span class="info-tag">{{ detail.record?.created_at }}</span>
        </div>
      </div>

      <div class="detail-output" v-if="detail.output">
        <div v-if="detail.output.weather_summary" class="section-card">
          <h4>☁️ 天气预警</h4>
          <p>{{ detail.output.weather_summary }}</p>
        </div>
        <div v-if="detail.output.route_summary" class="section-card">
          <h4>🗺 路线建议</h4>
          <p>{{ detail.output.route_summary }}</p>
        </div>
        <div v-if="detail.output.amap_route_url || mapExport?.image_url" class="section-card">
          <h4>📍 高德路线</h4>
          <img v-if="mapExport?.image_url" :src="mapExport.image_url" class="route-map-img" alt="路线图" />
          <a v-if="detail.output.amap_route_url || mapExport?.amap_route_url" :href="detail.output.amap_route_url || mapExport.amap_route_url" target="_blank" class="amap-link">打开高德路线 →</a>
        </div>
        <div v-if="detail.output.attractions_summary" class="section-card">
          <h4>🏞 途径景点</h4>
          <p>{{ detail.output.attractions_summary }}</p>
        </div>
        <div v-if="detail.output.realtime_info_summary" class="section-card">
          <h4>📡 实时信息</h4>
          <p>{{ detail.output.realtime_info_summary }}</p>
        </div>
        <div v-if="detail.output.final_markdown" class="section-card markdown">
          <div v-html="renderedMarkdown"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { planningApi } from '@/api/planning'
import { useLoading } from '@/composables/useLoading'
import { marked } from 'marked'

const route = useRoute()
const { loading, withLoading } = useLoading()
const detail = ref(null)

const statusMap = { pending: '等待中', streaming: '生成中', completed: '已完成', failed: '失败', canceled: '已取消' }
const transportMap = { driving: '自驾', transit: '公交', walking: '步行', cycling: '骑行', mixed: '混合' }

function statusLabel(s) { return statusMap[s] || s }
function transportLabel(t) { return transportMap[t] || t }

const renderedMarkdown = computed(() => {
  if (detail.value?.output?.final_markdown) {
    return marked.parse(detail.value.output.final_markdown)
  }
  return ''
})

const mapExport = computed(() => detail.value?.snapshots?.map_exports?.[0] || null)

const fetchDetail = withLoading(async () => {
  const res = await planningApi.getRecordDetail(route.params.recordId)
  detail.value = res.data
})

onMounted(() => fetchDetail())
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
  margin-bottom: 24px;

  h2 {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 12px;
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

.section-card {
  background: $content-bg;
  border-radius: $radius-lg;
  padding: 20px 24px;
  margin-bottom: 12px;
  box-shadow: $shadow-card;

  h4 {
    font-size: 15px;
    font-weight: 600;
    color: $text-secondary;
    margin-bottom: 10px;
  }

  p { line-height: 1.7; }
}

.amap-link {
  color: $color-link;
  font-weight: 500;
}

.route-map-img {
  width: 100%;
  border-radius: $radius-sm;
  border: 1px solid $border-light;
  margin-bottom: 10px;
}

.markdown :deep(h2) { font-size: 18px; margin: 16px 0 8px; }
.markdown :deep(p) { margin-bottom: 10px; }
</style>
