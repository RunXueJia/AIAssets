<template>
  <div class="result-page" v-loading="loading">
    <template v-if="detail">
      <h2>规划结果</h2>
      <div class="result-meta">
        <span>{{ detail.record?.origin_text }} → {{ detail.record?.destination_text }}</span>
        <span class="status-badge" :class="detail.record?.status">{{ statusLabel(detail.record?.status) }}</span>
      </div>
      <div class="output-wrap" v-if="detail.output">
        <div v-if="detail.output.final_markdown" class="markdown-body" v-html="renderedMarkdown"></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { planningApi } from '@/api/planning'
import { useLoading } from '@/composables/useLoading'
import { marked } from 'marked'

const route = useRoute()
const { loading, withLoading } = useLoading()
const detail = ref(null)

const statusMap = { pending: '等待中', streaming: '生成中', completed: '已完成', failed: '失败', canceled: '已取消' }
function statusLabel(s) { return statusMap[s] || s }

const renderedMarkdown = computed(() => {
  if (detail.value?.output?.final_markdown) return marked.parse(detail.value.output.final_markdown)
  return ''
})

const fetchDetail = withLoading(async () => {
  const res = await planningApi.getRecordDetail(route.params.recordId)
  detail.value = res.data
})

onMounted(() => fetchDetail())
</script>

<style lang="scss" scoped>
.result-page { max-width: 720px; margin: 0 auto; }

.result-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  color: $text-secondary;
  font-size: $font-size-sm;
}

.status-badge {
  font-size: $font-size-xs;
  padding: 3px 10px;
  border-radius: 12px;
  &.completed { background: rgba($color-success, 0.1); color: $color-success; }
  &.failed { background: rgba($color-danger, 0.1); color: $color-danger; }
}
</style>
