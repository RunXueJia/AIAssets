<template>
  <div class="generation-process">
    <page-header :title="`生成过程 - ${taskId}`">
      <template #actions>
        <el-button @click="$router.push('/generation/tasks')">返回任务列表</el-button>
      </template>
    </page-header>

    <el-row :gutter="16">
      <el-col :span="16">
        <!-- Stage progress -->
        <el-card class="stage-card">
          <stage-timeline :current-stage="currentStage" :progress="progress" :stages="stages" />
        </el-card>

        <!-- Text delta -->
        <el-card v-if="deltaText" class="delta-card">
          <template #header><span>实时生成内容</span></template>
          <div class="delta-text">{{ deltaText }}</div>
        </el-card>

        <!-- Results -->
        <el-card v-if="results.length" class="result-card">
          <template #header><span>阶段结果</span></template>
          <div v-for="(r, i) in results" :key="i" class="result-item">
            <el-tag size="small" :type="r.type === 'script' ? 'success' : 'info'">{{ r.type }}</el-tag>
            <span class="result-msg">{{ r.message }}</span>
            <el-button v-if="r.content_id" size="small" type="primary" link @click="goToContent(r)">
              查看详情
            </el-button>
          </div>
        </el-card>

        <!-- Error -->
        <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon :closable="false" class="error-alert">
          <template #default>
            <el-button size="small" @click="$router.push(`/generation/tasks`)">查看任务详情</el-button>
          </template>
        </el-alert>
      </el-col>

      <el-col :span="8">
        <!-- Source feed -->
        <el-card class="source-card">
          <template #header><span>抓取来源 ({{ sources.length }})</span></template>
          <div v-if="sources.length === 0" class="source-empty">等待抓取...</div>
          <div v-for="src in sources" :key="src.id" class="source-item">
            <div class="source-title">{{ src.title }}</div>
            <div class="source-site">{{ src.site_name }}</div>
            <div class="source-summary">{{ src.summary }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTaskDetail } from '@/api/generation'
import { SSEClient, createStreamUrl } from '@/sse/client'
import { STAGE_NAMES } from '@/utils/constants'
import PageHeader from '@/components/common/PageHeader.vue'
import StageTimeline from '@/components/generation/StageTimeline.vue'

const route = useRoute()
const router = useRouter()
const taskId = route.params.id

const stages = Object.entries(STAGE_NAMES).map(([value, label]) => ({ value, label }))
const currentStage = ref('create_task')
const progress = ref(0)
const deltaText = ref('')
const sources = reactive([])
const results = reactive([])
const errorMsg = ref('')
let sseClient = null

function goToContent(result) {
  if (result.type === 'script') {
    router.push(`/script/detail/${result.content_id}`)
  }
}

async function restoreState() {
  try {
    const task = await getTaskDetail(taskId)
    currentStage.value = task.current_stage || 'create_task'
    progress.value = task.progress || 0
    errorMsg.value = task.error_message || ''
    if (task.status === 'success' || task.status === 'failed' || task.status === 'cancelled') {
      // Task already finished, no need to connect SSE
      return false
    }
    return task.status === 'pending' || task.status === 'running' || task.status === 'retrying'
  } catch {
    errorMsg.value = '加载任务详情失败'
    return false
  }
}

function connectSSE() {
  const url = createStreamUrl(taskId)
  sseClient = new SSEClient(url, {
    start: (data) => {
      currentStage.value = 'create_task'
      progress.value = 5
    },
    stage: (data) => {
      currentStage.value = data.stage
      progress.value = Math.min(data.progress || 0, 95)
    },
    source: (data) => {
      sources.unshift(data)
    },
    delta: (data) => {
      deltaText.value += data.text || ''
    },
    result: (data) => {
      results.push(data)
      progress.value = Math.min(progress.value + 5, 98)
    },
    error: (data) => {
      errorMsg.value = data.message || '生成过程中出现异常'
    },
    done: (data) => {
      currentStage.value = 'completed'
      progress.value = 100
      errorMsg.value = data.status === 'failed' ? (data.message || '任务执行失败') : ''
    },
  })
  sseClient.connect()
}

onMounted(async () => {
  const shouldConnect = await restoreState()
  if (shouldConnect) {
    connectSSE()
  }
})

onUnmounted(() => {
  sseClient?.close()
})
</script>

<style scoped lang="scss">
.stage-card, .delta-card, .result-card, .source-card {
  margin-bottom: 16px;
}

.delta-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #303133;
  max-height: 300px;
  overflow-y: auto;
  font-size: 14px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  &:last-child { border-bottom: none; }
}

.result-msg {
  flex: 1;
  color: #606266;
}

.error-alert {
  margin-bottom: 16px;
}

.source-empty {
  color: #909399;
  text-align: center;
  padding: 20px 0;
}

.source-item {
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  &:last-child { border-bottom: none; }
}

.source-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.source-site {
  font-size: 12px;
  color: #409eff;
  margin-bottom: 4px;
}

.source-summary {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}
</style>
