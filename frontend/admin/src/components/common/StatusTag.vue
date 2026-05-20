<template>
  <el-tag :type="tagType" :size="size">{{ label }}</el-tag>
</template>

<script setup>
import { computed } from 'vue'
import { STATUS_TAG_TYPE } from '@/utils/constants'

const props = defineProps({
  status: { type: String, required: true },
  map: { type: Object, default: null },
  size: { type: String, default: 'default' },
})

const label = computed(() => {
  if (props.map && props.map[props.status]) return props.map[props.status]
  return props.status
})

const tagType = computed(() => {
  return STATUS_TAG_TYPE[props.status] || 'info'
})
</script>
