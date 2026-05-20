<template>
  <el-card>
    <el-table :data="localItems" stripe>
      <el-table-column label="序号" width="60" type="index" />
      <el-table-column prop="start_time" label="开始时间" width="130">
        <template #default="{ row, $index }">
          <el-input v-model="localItems[$index].start_time" size="small" :disabled="readonly" />
        </template>
      </el-table-column>
      <el-table-column prop="end_time" label="结束时间" width="130">
        <template #default="{ row, $index }">
          <el-input v-model="localItems[$index].end_time" size="small" :disabled="readonly" />
        </template>
      </el-table-column>
      <el-table-column prop="text" label="字幕内容" min-width="300">
        <template #default="{ row, $index }">
          <el-input v-model="localItems[$index].text" size="small" :disabled="readonly" />
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, watch } from 'vue'

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
  emit('update', items.map(({ id, start_time, end_time, text }) => ({ id, start_time, end_time, text })))
}, { deep: true })
</script>
