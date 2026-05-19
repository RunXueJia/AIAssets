<template>
  <el-tag
    :type="meta.type"
    effect="light"
    round
  >
    {{ meta.label }}
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'
import { getStatusMeta } from '@/utils/status'

const props = defineProps({
  status: {
    type: String,
    default: ''
  }
})

const meta = computed(() => getStatusMeta(props.status))
</script>
