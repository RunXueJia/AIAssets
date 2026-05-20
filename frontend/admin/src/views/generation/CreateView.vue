<template>
  <div class="generation-create">
    <page-header title="内容生成" />

    <el-card>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="160px" size="large">
        <el-form-item label="你想做什么内容" prop="direction">
          <el-input v-model="form.direction" type="textarea" :rows="3" placeholder="例如：介绍 AI 工具在日常办公中的使用技巧，帮助职场人提升效率" maxlength="500" show-word-limit />
        </el-form-item>

        <el-form-item label="这次想讲什么主题">
          <el-input v-model="form.topic" placeholder="例如：AI 写周报，留空则由系统自动判断" maxlength="200" />
        </el-form-item>

        <el-form-item label="主要给谁看">
          <el-input v-model="form.audience" placeholder="例如：普通职场人、新手设计师，留空则默认泛人群" maxlength="100" />
        </el-form-item>

        <el-form-item label="一次生成几条">
          <el-input-number v-model="form.count" :min="1" :max="20" />
          <span class="form-hint">建议 3-5 条，生成时间约 2-5 分钟</span>
        </el-form-item>

        <el-form-item label="内容更适合哪个栏目">
          <el-select v-model="form.column" style="width: 280px">
            <el-option v-for="col in columns" :key="col.value" :label="col.label" :value="col.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="这次要生成到哪一步">
          <el-radio-group v-model="form.generation_type">
            <el-radio value="topics_only">只生成选题</el-radio>
            <el-radio value="topics_and_script">生成选题和脚本</el-radio>
            <el-radio value="full_script_storyboard">完整生成脚本和分镜</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="是否现在开始">
          <el-radio-group v-model="form.start_mode">
            <el-radio value="now">现在开始生成</el-radio>
            <el-radio value="draft">保存为草稿，稍后开始</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit" size="large">
            开始生成内容
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createTask } from '@/api/generation'
import { COLUMNS } from '@/utils/constants'
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)

const columns = COLUMNS

const form = reactive({
  direction: '',
  topic: '',
  audience: '',
  count: 5,
  column: 'auto',
  generation_type: 'full_script_storyboard',
  start_mode: 'now',
})

const rules = {
  direction: [{ required: true, message: '请描述你想做什么内容', trigger: 'blur' }],
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const result = await createTask({
      direction: form.direction,
      topic: form.topic || undefined,
      audience: form.audience || undefined,
      count: form.count,
      column: form.column,
      generation_type: form.generation_type,
      start_mode: form.start_mode,
    })

    if (form.start_mode === 'now') {
      router.push(`/generation/process/${result.task_id}`)
    } else {
      ElMessage.success('已保存为草稿')
      router.push('/generation/tasks')
    }
  } catch {
    // error handled by request interceptor
  } finally {
    submitting.value = false
  }
}

function handleReset() {
  formRef.value?.resetFields()
  form.direction = ''
  form.topic = ''
  form.audience = ''
  form.count = 5
  form.column = 'auto'
  form.generation_type = 'full_script_storyboard'
  form.start_mode = 'now'
}
</script>

<style scoped lang="scss">
.form-hint {
  margin-left: 12px;
  font-size: 13px;
  color: #909399;
}
</style>
