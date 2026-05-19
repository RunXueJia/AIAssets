<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">
          内容生产
        </h1>
        <p class="page-subtitle">
          覆盖内容方向、栏目、选题、脚本、分镜与流式生成入口。
        </p>
      </div>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane
        label="内容方向"
        name="channels"
      >
        <DataPanel
          :items="channels.items"
          :total="channels.total"
          :loading="loading"
          :page="query.page"
          :page-size="query.page_size"
          @search="handleSearch"
          @update:page="setPage"
          @update:page-size="setPageSize"
        >
          <template #actions>
            <el-button
              type="primary"
              :icon="Plus"
              @click="openChannelForm()"
            >
              新增方向
            </el-button>
          </template>
          <el-table-column
            prop="name"
            label="名称"
            min-width="180"
          />
          <el-table-column
            prop="target_audience"
            label="受众"
            min-width="180"
          />
          <el-table-column
            prop="daily_topic_quota"
            label="每日目标"
            width="100"
          />
          <el-table-column
            label="状态"
            width="100"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="130"
          >
            <template #default="{ row }">
              <el-button
                text
                type="primary"
                @click="openChannelForm(row)"
              >
                编辑
              </el-button>
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>

      <el-tab-pane
        label="栏目"
        name="columns"
      >
        <DataPanel
          :items="columns.items"
          :total="columns.total"
          :loading="loading"
          @search="handleSearch"
        >
          <el-table-column
            prop="name"
            label="栏目"
            min-width="180"
          />
          <el-table-column
            prop="description"
            label="说明"
            min-width="240"
          />
          <el-table-column
            prop="default_duration"
            label="默认时长"
            width="100"
          />
          <el-table-column
            label="状态"
            width="100"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>

      <el-tab-pane
        label="选题"
        name="topics"
      >
        <DataPanel
          :items="topics.items"
          :total="topics.total"
          :loading="loading"
          @search="handleSearch"
        >
          <template #actions>
            <PermissionGate permission="content:topic:generate">
              <el-button
                type="primary"
                :icon="MagicStick"
                @click="generatorVisible = true"
              >
                生成选题
              </el-button>
            </PermissionGate>
          </template>
          <el-table-column
            prop="title"
            label="标题"
            min-width="220"
          />
          <el-table-column
            prop="audience"
            label="受众"
            width="150"
          />
          <el-table-column
            prop="angle"
            label="角度"
            min-width="160"
          />
          <el-table-column
            label="关键词"
            min-width="160"
          >
            <template #default="{ row }">
              {{ row.keywords?.join(' / ') }}
            </template>
          </el-table-column>
          <el-table-column
            label="状态"
            width="100"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>

      <el-tab-pane
        label="脚本"
        name="scripts"
      >
        <DataPanel
          :items="scripts.items"
          :total="scripts.total"
          :loading="loading"
          @search="handleSearch"
        >
          <el-table-column
            prop="platform_title"
            label="平台标题"
            min-width="220"
          />
          <el-table-column
            prop="hook"
            label="开头钩子"
            min-width="180"
          />
          <el-table-column
            label="风险标记"
            min-width="200"
          >
            <template #default="{ row }">
              {{ row.risk_flags?.join(' / ') || '-' }}
            </template>
          </el-table-column>
          <el-table-column
            label="状态"
            width="110"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>

      <el-tab-pane
        label="分镜"
        name="storyboards"
      >
        <DataPanel
          :items="storyboards.items"
          :total="storyboards.total"
          :loading="loading"
          @search="handleSearch"
        >
          <el-table-column
            prop="scene_index"
            label="镜头"
            width="80"
          />
          <el-table-column
            prop="duration_seconds"
            label="秒数"
            width="80"
          />
          <el-table-column
            prop="voiceover"
            label="旁白"
            min-width="200"
          />
          <el-table-column
            prop="visual_prompt"
            label="画面建议"
            min-width="220"
          />
          <el-table-column
            prop="motion_hint"
            label="动效"
            min-width="160"
          />
        </DataPanel>
      </el-tab-pane>
    </el-tabs>

    <el-drawer
      v-model="channelFormVisible"
      title="内容方向"
      size="520"
    >
      <el-form
        :model="channelForm"
        label-position="top"
      >
        <el-form-item label="名称">
          <el-input v-model="channelForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="channelForm.description"
            type="textarea"
          />
        </el-form-item>
        <el-form-item label="受众">
          <el-input v-model="channelForm.target_audience" />
        </el-form-item>
        <el-form-item label="语气">
          <el-input v-model="channelForm.tone" />
        </el-form-item>
        <el-form-item label="每日目标产量">
          <el-input-number
            v-model="channelForm.daily_topic_quota"
            :min="1"
          />
        </el-form-item>
        <el-button
          type="primary"
          @click="saveChannel"
        >
          保存
        </el-button>
      </el-form>
    </el-drawer>

    <el-drawer
      v-model="generatorVisible"
      title="选题流式生成"
      size="680"
    >
      <el-form
        :model="generationForm"
        label-position="top"
        class="generation-form"
      >
        <el-form-item label="栏目">
          <el-input v-model="generationForm.column_name" />
        </el-form-item>
        <el-form-item label="生成数量">
          <el-input-number
            v-model="generationForm.count"
            :min="1"
            :max="50"
          />
        </el-form-item>
        <el-form-item label="关键词种子">
          <el-input v-model="generationForm.keyword_seeds" />
        </el-form-item>
      </el-form>
      <SseOutputPanel
        title="选题生成流"
        :text="stream.text"
        :raw="stream.raw"
        :stats="stream.stats"
        :streaming="stream.streaming"
        :interrupted="stream.interrupted"
        @start="startTopicStream"
        @stop="stopStream"
      />
    </el-drawer>
  </div>
</template>

<script setup>
import { MagicStick, Plus } from '@element-plus/icons-vue'
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { contentApi } from '@/api'
import DataPanel from '@/components/DataPanel.vue'
import PermissionGate from '@/components/PermissionGate.vue'
import SseOutputPanel from '@/components/SseOutputPanel.vue'
import StatusTag from '@/components/StatusTag.vue'
import { streamOpenAiSse } from '@/utils/sseClient'

const tab = ref('channels')
const loading = ref(false)
const query = reactive({ page: 1, page_size: 20, keyword: '' })
const channels = reactive({ items: [], total: 0 })
const columns = reactive({ items: [], total: 0 })
const topics = reactive({ items: [], total: 0 })
const scripts = reactive({ items: [], total: 0 })
const storyboards = reactive({ items: [], total: 0 })
const channelFormVisible = ref(false)
const generatorVisible = ref(false)
const channelForm = reactive({})
const generationForm = reactive({ column_name: '一分钟 AI 办公', count: 5, keyword_seeds: 'AI 写周报' })
const streamController = ref(null)
const stream = reactive({
  text: '',
  raw: '',
  streaming: false,
  interrupted: false,
  stats: { chunkCount: 0, firstTokenMs: 0 }
})

async function load() {
  loading.value = true
  try {
    const params = { ...query }
    const loaders = {
      channels: () => contentApi.getChannels(params).then(assignList(channels)),
      columns: () => contentApi.getColumns(params).then(assignList(columns)),
      topics: () => contentApi.getTopics(params).then(assignList(topics)),
      scripts: () => contentApi.getScripts(params).then(assignList(scripts)),
      storyboards: () => contentApi.getStoryboards(params).then(assignList(storyboards))
    }
    await loaders[tab.value]()
  } finally {
    loading.value = false
  }
}

function assignList(target) {
  return (data) => {
    target.items = data.items
    target.total = data.total
  }
}

function handleSearch(keyword) {
  query.keyword = keyword
  query.page = 1
  load()
}

function setPage(page) {
  query.page = page
  load()
}

function setPageSize(pageSize) {
  query.page_size = pageSize
  load()
}

function openChannelForm(row = {}) {
  Object.assign(channelForm, {
    id: row.id,
    name: row.name || '',
    description: row.description || '',
    target_audience: row.target_audience || '',
    tone: row.tone || '',
    daily_topic_quota: row.daily_topic_quota || 20
  })
  channelFormVisible.value = true
}

async function saveChannel() {
  await contentApi.saveChannel(channelForm)
  ElMessage.success('内容方向已保存')
  channelFormVisible.value = false
  load()
}

async function startTopicStream() {
  stream.text = ''
  stream.raw = ''
  stream.interrupted = false
  stream.streaming = true
  stream.stats = { chunkCount: 0, firstTokenMs: 0 }
  streamController.value = new AbortController()
  try {
    await streamOpenAiSse(
      '/topics/stream_generate_topics',
      {
        column_name: generationForm.column_name,
        count: generationForm.count,
        keyword_seeds: generationForm.keyword_seeds
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean)
      },
      {
        onFirstToken: ({ firstTokenMs }) => {
          stream.stats.firstTokenMs = Math.round(firstTokenMs)
        },
        onChunk: (chunk) => {
          stream.raw += `data: ${JSON.stringify(chunk)}\n\n`
          stream.stats.chunkCount += 1
        },
        onDelta: (_delta, context) => {
          stream.text = context.text
        },
        onDone: () => {
          stream.streaming = false
        },
        onInterrupted: () => {
          stream.interrupted = true
        }
      },
      { controller: streamController.value }
    )
  } catch (error) {
    stream.interrupted = true
    ElMessage.error(error.message || '流式生成失败')
  } finally {
    stream.streaming = false
    streamController.value = null
  }
}

function stopStream() {
  streamController.value?.abort()
  stream.streaming = false
  stream.interrupted = true
}

watch(tab, () => {
  query.keyword = ''
  query.page = 1
  load()
})

onMounted(load)
</script>

<style scoped lang="scss">
.generation-form {
  margin-bottom: 16px;
}
</style>
