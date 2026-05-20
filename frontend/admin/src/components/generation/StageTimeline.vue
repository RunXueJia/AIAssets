<template>
  <div class="stage-timeline">
    <el-steps :active="activeIndex" align-center finish-status="success" process-status="process">
      <el-step v-for="s in stages" :key="s.value" :title="s.label" :status="getStepStatus(s.value)" />
    </el-steps>
    <div class="progress-bar">
      <el-progress :percentage="progress" :stroke-width="8" :show-text="true" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentStage: { type: String, required: true },
  progress: { type: Number, default: 0 },
  stages: { type: Array, required: true },
})

const activeIndex = computed(() => {
  const idx = props.stages.findIndex((s) => s.value === props.currentStage)
  return idx >= 0 ? idx : 0
})

function getStepStatus(stageValue) {
  const idx = props.stages.findIndex((s) => s.value === stageValue)
  const currentIdx = activeIndex.value
  if (idx < currentIdx) return 'success'
  if (idx === currentIdx) return 'process'
  return 'wait'
}
</script>

<style scoped lang="scss">
.stage-timeline {
  padding: 10px 0;
}

.progress-bar {
  margin-top: 24px;
  padding: 0 40px;
}
</style>
