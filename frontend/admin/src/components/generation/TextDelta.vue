<template>
  <div class="text-delta">
    <div class="delta-content">{{ text }}</div>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: '' },
})
</script>

<style scoped lang="scss">
.delta-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #303133;
  font-size: 14px;
  min-height: 60px;
}
</style>
