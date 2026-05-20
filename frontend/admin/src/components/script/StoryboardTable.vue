<template>
  <el-card>
    <el-table :data="localItems" stripe>
      <el-table-column prop="shot_no" label="镜号" width="70" />
      <el-table-column prop="duration_seconds" label="时长(秒)" width="90">
        <template #default="{ row, $index }">
          <el-input-number v-model="localItems[$index].duration_seconds" :min="1" :max="120" size="small" controls-position="right" :disabled="readonly" />
        </template>
      </el-table-column>
      <el-table-column prop="voiceover" label="旁白/口播" min-width="200">
        <template #default="{ row, $index }">
          <el-input v-model="localItems[$index].voiceover" size="small" :disabled="readonly" />
        </template>
      </el-table-column>
      <el-table-column prop="subtitle" label="字幕" width="150">
        <template #default="{ row, $index }">
          <el-input v-model="localItems[$index].subtitle" size="small" :disabled="readonly" />
        </template>
      </el-table-column>
      <el-table-column prop="visual_type" label="画面类型" width="120">
        <template #default="{ row, $index }">
          <el-select v-model="localItems[$index].visual_type" size="small" :disabled="readonly">
            <el-option v-for="(label, value) in VISUAL_TYPES" :key="value" :label="label" :value="value" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="material_suggestion" label="素材建议" min-width="150">
        <template #default="{ row, $index }">
          <el-input v-model="localItems[$index].material_suggestion" size="small" :disabled="readonly" />
        </template>
      </el-table-column>
      <el-table-column prop="motion_suggestion" label="动效建议" width="120">
        <template #default="{ row, $index }">
          <el-input v-model="localItems[$index].motion_suggestion" size="small" :disabled="readonly" />
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import { VISUAL_TYPES } from '@/utils/constants'

const props = defineProps({
  items: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['update'])

const localItems = ref([])

watch(
  () => props.items,
  (items) => {
    localItems.value = items.map((item) => ({ ...item }))
  },
  { immediate: true },
)

watch(localItems, (items) => {
  emit('update', items.map(({ id, shot_no, duration_seconds, voiceover, subtitle, visual_type, material_suggestion, motion_suggestion }) => ({
    id, shot_no, duration_seconds, voiceover, subtitle, visual_type, material_suggestion, motion_suggestion,
  })))
}, { deep: true })
</script>
