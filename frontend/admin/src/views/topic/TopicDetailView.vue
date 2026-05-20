<template>
  <div class="topic-detail">
    <page-header title="选题详情">
      <template #actions>
        <el-button @click="$router.back()">返回列表</el-button>
        <el-button v-if="topic.status === 'draft'" type="success" @click="approve">通过</el-button>
        <el-button v-if="topic.status === 'draft'" type="danger" @click="reject">驳回</el-button>
        <el-button type="primary" @click="generateScript">基于此选题生成脚本</el-button>
      </template>
    </page-header>

    <el-card v-loading="loading">
      <template v-if="topic.id">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题" :span="2">{{ topic.title }}</el-descriptions-item>
          <el-descriptions-item label="受众">{{ topic.audience }}</el-descriptions-item>
          <el-descriptions-item label="栏目">{{ topic.column }}</el-descriptions-item>
          <el-descriptions-item label="角度">{{ topic.angle }}</el-descriptions-item>
          <el-descriptions-item label="时长">{{ topic.duration_seconds }} 秒</el-descriptions-item>
          <el-descriptions-item label="状态">
            <status-tag :status="topic.status" :map="TOPIC_STATUS" />
          </el-descriptions-item>
          <el-descriptions-item label="关键词" :span="2">
            <el-tag v-for="k in topic.keywords" :key="k" size="small" class="keyword-tag">{{ k }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="生成原因" :span="2">{{ topic.reason }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ topic.created_at }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { getTopicDetail, changeTopicStatus, generateScript as generateScriptApi } from '@/api/topic'
import { TOPIC_STATUS } from '@/utils/constants'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const topic = ref({})

async function fetchDetail() {
  loading.value = true
  try {
    topic.value = await getTopicDetail(route.params.id)
  } catch {}
  loading.value = false
}

async function approve() {
  try {
    await changeTopicStatus(topic.value.id, 'approved', '')
    topic.value.status = 'approved'
  } catch {}
}

async function reject() {
  try {
    await ElMessageBox.prompt('请输入驳回原因', '驳回选题', { type: 'warning' })
    await changeTopicStatus(topic.value.id, 'rejected', '')
    topic.value.status = 'rejected'
  } catch {}
}

async function generateScript() {
  try {
    const result = await generateScriptApi(topic.value.id, 'now')
    router.push(`/generation/process/${result.task_id}`)
  } catch {}
}

onMounted(() => fetchDetail())
</script>

<style scoped lang="scss">
.keyword-tag { margin-right: 8px; margin-bottom: 4px; }
</style>
