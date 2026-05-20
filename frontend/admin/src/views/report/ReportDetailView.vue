<template>
  <div class="report-detail">
    <page-header title="报告详情">
      <template #actions>
        <el-button @click="$router.back()">返回列表</el-button>
        <el-button type="primary" @click="exportReport('markdown')">导出 Markdown</el-button>
        <el-button type="primary" @click="exportReport('pdf')">导出 PDF</el-button>
      </template>
    </page-header>

    <el-card v-loading="loading">
      <template v-if="report.id">
        <div class="markdown-body" v-html="renderedMarkdown" />
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getDailyReportDetail, getReportExportUrl } from '@/api/report'
import PageHeader from '@/components/common/PageHeader.vue'

const route = useRoute()
const loading = ref(false)
const report = ref({})

const renderedMarkdown = computed(() => {
  const md = report.value.markdown || ''
  return md
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
})

async function fetchDetail() {
  loading.value = true
  try {
    report.value = await getDailyReportDetail(route.params.id)
  } catch {}
  loading.value = false
}

function exportReport(format) {
  const token = localStorage.getItem('token')
  const url = getReportExportUrl(report.value.id, format)
  const a = document.createElement('a')
  a.href = `${url}?token=${token}`
  a.download = ''
  a.click()
}

onMounted(() => fetchDetail())
</script>

<style scoped lang="scss">
.markdown-body {
  line-height: 1.8;
  color: #303133;
  h2, h3, h4 { margin-top: 16px; margin-bottom: 8px; color: #303133; }
}
</style>
