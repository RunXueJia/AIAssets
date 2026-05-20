<template>
  <el-card>
    <el-form :model="form" label-width="120px">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="标题">
            <el-input v-model="form.title" :disabled="readonly" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="平台标题">
            <el-input v-model="form.platform_title" :disabled="readonly" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="开头钩子">
        <el-input v-model="form.hook" type="textarea" :rows="2" :disabled="readonly" />
      </el-form-item>
      <el-form-item label="痛点">
        <el-input v-model="form.pain_point" type="textarea" :rows="2" :disabled="readonly" />
      </el-form-item>
      <el-form-item label="核心方法">
        <el-input v-model="form.method" type="textarea" :rows="2" :disabled="readonly" />
      </el-form-item>
      <el-form-item label="操作步骤">
        <div v-for="(step, i) in form.steps" :key="i" class="step-item">
          <el-input v-model="form.steps[i]" :disabled="readonly" style="margin-bottom: 8px">
            <template #prepend>步骤 {{ i + 1 }}</template>
          </el-input>
        </div>
      </el-form-item>
      <el-form-item label="示例">
        <el-input v-model="form.example" type="textarea" :rows="2" :disabled="readonly" />
      </el-form-item>
      <el-form-item label="总结">
        <el-input v-model="form.summary" type="textarea" :rows="2" :disabled="readonly" />
      </el-form-item>
      <el-form-item label="行动号召">
        <el-input v-model="form.cta" :disabled="readonly" />
      </el-form-item>
      <el-form-item label="简介">
        <el-input v-model="form.description" type="textarea" :rows="2" :disabled="readonly" />
      </el-form-item>
      <el-form-item label="标签">
        <el-input v-model="tagsStr" :disabled="readonly" placeholder="用逗号分隔" />
      </el-form-item>
      <el-form-item label="封面文案">
        <el-input v-model="form.cover_text" :disabled="readonly" />
      </el-form-item>
      <el-form-item label="置顶评论">
        <el-input v-model="form.pinned_comment" :disabled="readonly" />
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'

const props = defineProps({
  script: { type: Object, default: null },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['update'])

const form = reactive({
  title: '',
  platform_title: '',
  hook: '',
  pain_point: '',
  method: '',
  steps: [],
  example: '',
  summary: '',
  cta: '',
  description: '',
  tags: [],
  cover_text: '',
  pinned_comment: '',
})

const tagsStr = computed({
  get: () => (form.tags || []).join('，'),
  set: (val) => { form.tags = val.split(/[,，]/).map((t) => t.trim()).filter(Boolean) },
})

watch(
  () => props.script,
  (s) => {
    if (s) Object.assign(form, {
      title: s.title || '',
      platform_title: s.platform_title || '',
      hook: s.hook || '',
      pain_point: s.pain_point || '',
      method: s.method || '',
      steps: s.steps ? [...s.steps] : [],
      example: s.example || '',
      summary: s.summary || '',
      cta: s.cta || '',
      description: s.description || '',
      tags: s.tags ? [...s.tags] : [],
      cover_text: s.cover_text || '',
      pinned_comment: s.pinned_comment || '',
    })
  },
  { immediate: true },
)

watch(form, () => {
  emit('update', { ...form })
}, { deep: true })
</script>

<style scoped lang="scss">
.step-item {
  width: 100%;
}
</style>
