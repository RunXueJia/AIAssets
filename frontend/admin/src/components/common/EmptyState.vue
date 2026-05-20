<template>
  <div class="empty-state">
    <el-empty :description="description" :image-size="imageSize" />
    <slot />
  </div>
</template>

<script setup>
defineProps({
  description: { type: String, default: '暂无数据' },
  imageSize: { type: Number, default: 120 },
})
</script>

<style scoped lang="scss">
.empty-state {
  padding: 60px 0;
  text-align: center;
}
</style>
