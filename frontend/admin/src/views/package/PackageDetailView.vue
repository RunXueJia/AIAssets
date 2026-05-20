<template>
  <div class="package-detail">
    <page-header title="发布包详情">
      <template #actions>
        <el-button @click="$router.back()">返回列表</el-button>
        <el-button type="primary" @click="downloadPackage">下载发布包</el-button>
      </template>
    </page-header>

    <el-card v-loading="loading">
      <template v-if="detail.id">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题" :span="2">{{ detail.title }}</el-descriptions-item>
          <el-descriptions-item label="平台标题">{{ detail.platform_title }}</el-descriptions-item>
          <el-descriptions-item label="发布时间">{{ detail.created_at }}</el-descriptions-item>
          <el-descriptions-item label="简介" :span="2">{{ detail.description }}</el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <el-tag v-for="t in detail.tags" :key="t" size="small" style="margin-right: 4px">{{ t }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="置顶评论" :span="2">{{ detail.pinned_comment }}</el-descriptions-item>
        </el-descriptions>

        <div class="section">
          <h4>视频文件</h4>
          <p>{{ detail.video_file?.name || '-' }}</p>
          <el-button v-if="detail.video_file?.download_url" size="small" type="primary" @click="downloadFile(detail.video_file.download_url)">下载视频</el-button>
        </div>

        <div class="section">
          <h4>封面图</h4>
          <img v-if="detail.cover_file?.download_url" :src="detail.cover_file.download_url" class="cover-preview" />
        </div>

        <div class="section">
          <h4>口播稿</h4>
          <div class="script-text">{{ detail.script_text || '-' }}</div>
        </div>

        <div class="section">
          <h4>资料包草稿</h4>
          <div class="script-text">{{ detail.download_draft || '-' }}</div>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getPackageDetail, getPackageDownloadUrl } from '@/api/package'
import PageHeader from '@/components/common/PageHeader.vue'

const route = useRoute()
const loading = ref(false)
const detail = ref({})

async function fetchDetail() {
  loading.value = true
  try {
    detail.value = await getPackageDetail(route.params.id)
  } catch {}
  loading.value = false
}

function downloadPackage() {
  const token = localStorage.getItem('token')
  const url = detail.value.download_url || getPackageDownloadUrl(detail.value.id)
  const a = document.createElement('a')
  a.href = `${url}?token=${token}`
  a.download = ''
  a.click()
}

function downloadFile(url) {
  const token = localStorage.getItem('token')
  const a = document.createElement('a')
  a.href = `${url}?token=${token}`
  a.download = ''
  a.click()
}

onMounted(() => fetchDetail())
</script>

<style scoped lang="scss">
.section { margin-top: 24px; }
.section h4 { font-size: 15px; color: #303133; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0; }
.script-text { white-space: pre-wrap; color: #606266; line-height: 1.8; font-size: 14px; }
.cover-preview { max-width: 200px; border-radius: 4px; }
</style>
