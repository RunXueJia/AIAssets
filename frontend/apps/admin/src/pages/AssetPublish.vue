<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">
          资产与发布
        </h1>
        <p class="page-subtitle">
          管理视频、资料包、知识卡片和平台发布队列。
        </p>
      </div>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane
        label="视频资产"
        name="videos"
      >
        <DataPanel
          :items="videos.items"
          :total="videos.total"
          :loading="loading"
          @search="load"
        >
          <el-table-column
            prop="title"
            label="视频"
            min-width="220"
          />
          <el-table-column
            prop="column_name"
            label="栏目"
            width="160"
          />
          <el-table-column
            prop="resolution"
            label="分辨率"
            width="120"
          />
          <el-table-column
            prop="duration_seconds"
            label="时长"
            width="90"
          />
          <el-table-column
            label="状态"
            width="110"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="160"
          >
            <template #default="{ row }">
              <el-button
                text
                type="primary"
                @click="retry(row)"
              >
                重新合成
              </el-button>
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>
      <el-tab-pane
        label="资料包"
        name="downloads"
      >
        <DataPanel
          :items="downloads.items"
          :total="downloads.total"
          :loading="loading"
          @search="load"
        >
          <el-table-column
            prop="title"
            label="资料"
            min-width="220"
          />
          <el-table-column
            prop="type"
            label="类型"
            width="160"
          />
          <el-table-column
            prop="summary"
            label="摘要"
            min-width="260"
          />
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
        label="发布队列"
        name="publish"
      >
        <DataPanel
          :items="publish.items"
          :total="publish.total"
          :loading="loading"
          @search="load"
        >
          <el-table-column
            prop="title"
            label="发布包"
            min-width="220"
          />
          <el-table-column
            prop="platform"
            label="平台"
            width="130"
          />
          <el-table-column
            prop="package_status"
            label="素材包"
            width="120"
          />
          <el-table-column
            label="状态"
            width="120"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="220"
          >
            <template #default="{ row }">
              <el-button
                text
                type="success"
                @click="markPublished(row)"
              >
                标记发布
              </el-button>
              <el-button
                text
                @click="markOffline(row)"
              >
                下线
              </el-button>
            </template>
          </el-table-column>
        </DataPanel>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref, watch } from 'vue'

import DataPanel from '@/components/DataPanel.vue'
import StatusTag from '@/components/StatusTag.vue'
import { assetApi, publishApi } from '@/api'

const tab = ref('videos')
const loading = ref(false)
const videos = reactive({ items: [], total: 0 })
const downloads = reactive({ items: [], total: 0 })
const publish = reactive({ items: [], total: 0 })

async function load(keyword = '') {
  loading.value = true
  try {
    const loaders = {
      videos: () => assetApi.getVideos({ keyword }).then(assignList(videos)),
      downloads: () => assetApi.getDownloadAssets({ keyword }).then(assignList(downloads)),
      publish: () => publishApi.getQueue({ keyword }).then(assignList(publish))
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

async function retry(row) {
  await assetApi.retryRenderTask({ video_id: row.id })
  ElMessage.success('已创建重新合成任务')
}

async function markPublished(row) {
  await publishApi.markPublished({ publish_item_id: row.id, platform: row.platform, platform_url: '' })
  ElMessage.success('已标记为发布')
  load()
}

async function markOffline(row) {
  await publishApi.markOffline({ publish_item_id: row.id })
  ElMessage.success('已标记为下线')
  load()
}

watch(tab, () => load())
onMounted(load)
</script>
