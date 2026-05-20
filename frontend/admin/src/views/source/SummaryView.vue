<template>
  <div class="summary-view">
    <page-header title="素材汇总详情">
      <template #actions>
        <el-button @click="$router.back()">返回</el-button>
      </template>
    </page-header>

    <el-card v-loading="loading">
      <template v-if="summary">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="汇总标题" :span="2">{{ summary.title }}</el-descriptions-item>
          <el-descriptions-item label="内容摘要" :span="2">{{ summary.summary }}</el-descriptions-item>
          <el-descriptions-item label="来源总数">{{ summary.source_count }}</el-descriptions-item>
          <el-descriptions-item label="可用来源">{{ summary.usable_source_count }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ summary.created_at }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="summary.key_points && summary.key_points.length" class="section">
          <h4>关键要点</h4>
          <ul>
            <li v-for="(p, i) in summary.key_points" :key="i">{{ p }}</li>
          </ul>
        </div>
        <div v-if="summary.risk_notes && summary.risk_notes.length" class="section">
          <h4>风险提示</h4>
          <ul>
            <li v-for="(r, i) in summary.risk_notes" :key="i" style="color: #e6a23c">{{ r }}</li>
          </ul>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getSummaryDetail } from '@/api/source'
import PageHeader from '@/components/common/PageHeader.vue'

const route = useRoute()
const loading = ref(false)
const summary = ref(null)

onMounted(async () => {
  loading.value = true
  try {
    summary.value = await getSummaryDetail(route.params.id)
  } catch {}
  loading.value = false
})
</script>

<style scoped lang="scss">
.section { margin-top: 20px; }
.section h4 { font-size: 14px; color: #303133; margin-bottom: 8px; }
.section ul { padding-left: 20px; }
.section li { font-size: 13px; color: #606266; line-height: 1.8; }
</style>
