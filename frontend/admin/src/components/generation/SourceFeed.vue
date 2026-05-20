<template>
  <div class="source-feed">
    <div v-for="src in sources" :key="src.id" class="feed-item">
      <div class="feed-title">{{ src.title }}</div>
      <div class="feed-meta">
        <span class="feed-site">{{ src.site_name }}</span>
        <span v-if="src.relevance_reason" class="feed-reason">{{ src.relevance_reason }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  sources: { type: Array, default: () => [] },
})
</script>

<style scoped lang="scss">
.feed-item {
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  &:last-child { border-bottom: none; }
}

.feed-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.feed-meta {
  font-size: 12px;
}

.feed-site {
  color: #409eff;
  margin-right: 12px;
}

.feed-reason {
  color: #909399;
}
</style>
