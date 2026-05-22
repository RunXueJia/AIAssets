<template>
  <div class="record-detail" v-loading="loading">
    <div class="back-bar">
      <el-button text @click="$router.push('/records')">
        <el-icon><ArrowLeft /></el-icon> 返回记录列表
      </el-button>
    </div>

    <template v-if="detail">
      <h3>记录详情</h3>

      <!-- Record info -->
      <el-descriptions :column="2" border class="detail-table">
        <el-descriptions-item label="ID">{{ detail.record?.id }}</el-descriptions-item>
        <el-descriptions-item label="编号">{{ detail.record?.record_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(detail.record?.status)">{{ statusLabel(detail.record?.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="耗时">
          {{ detail.record?.duration_ms ? `${(detail.record.duration_ms / 1000).toFixed(1)}s` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="起点">{{ detail.input?.origin_text }}</el-descriptions-item>
        <el-descriptions-item label="目的地">{{ detail.input?.destination_text }}</el-descriptions-item>
        <el-descriptions-item label="交通方式">{{ transportLabel(detail.record?.transport_mode) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detail.record?.created_at }}</el-descriptions-item>
      </el-descriptions>

      <!-- Input -->
      <h4 class="section-title">输入参数</h4>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="范围">{{ detail.input?.range_text }}</el-descriptions-item>
        <el-descriptions-item label="出行日期">{{ detail.input?.travel_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="人数">{{ detail.input?.people_count }}</el-descriptions-item>
        <el-descriptions-item label="偏好">{{ (detail.input?.preferences || []).join('、') || '-' }}</el-descriptions-item>
        <el-descriptions-item label="避免项" :span="2">{{ (detail.input?.avoidances || []).join('、') || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- Output -->
      <h4 class="section-title">输出结果</h4>
      <div v-if="detail.output" class="output-sections">
        <div v-if="detail.output.weather_summary" class="info-block">
          <span class="block-label">天气：</span>{{ detail.output.weather_summary }}
        </div>
        <div v-if="detail.output.route_summary" class="info-block">
          <span class="block-label">路线：</span>{{ detail.output.route_summary }}
        </div>
        <div v-if="detail.output.amap_route_url || mapExport?.image_url" class="info-block">
          <span class="block-label">高德路线：</span>
          <a v-if="detail.output.amap_route_url || mapExport?.amap_route_url" :href="detail.output.amap_route_url || mapExport.amap_route_url" target="_blank">打开高德路线</a>
          <div v-if="mapExport?.image_url" class="route-map-preview">
            <img :src="mapExport.image_url" alt="路线图" />
          </div>
        </div>
        <div v-if="detail.output.attractions_summary" class="info-block">
          <span class="block-label">景点：</span>{{ detail.output.attractions_summary }}
        </div>
        <div v-if="detail.output.realtime_info_summary" class="info-block">
          <span class="block-label">实时信息：</span>{{ detail.output.realtime_info_summary }}
        </div>
        <div v-if="detail.output.risk_summary" class="info-block">
          <span class="block-label">风险提示：</span>{{ detail.output.risk_summary }}
        </div>
        <div v-if="detail.output.final_markdown" class="markdown-preview">
          <span class="block-label">最终 Markdown：</span>
          <pre class="md-content">{{ detail.output.final_markdown }}</pre>
        </div>
      </div>

      <!-- Errors -->
      <template v-if="detail.errors?.length">
        <h4 class="section-title">错误信息</h4>
        <el-table :data="detail.errors" border size="small">
          <el-table-column prop="stage" label="阶段" width="120" />
          <el-table-column prop="error_code" label="错误码" width="160" />
          <el-table-column prop="message" label="错误信息" min-width="240" />
        </el-table>
      </template>

      <!-- LLM Call Logs -->
      <template v-if="detail.llm_call_logs?.length">
        <h4 class="section-title">LLM 调用日志</h4>
        <el-table :data="detail.llm_call_logs" border size="small">
          <el-table-column prop="provider" label="供应商" width="140" />
          <el-table-column prop="model_name" label="模型" width="140" />
          <el-table-column prop="call_type" label="类型" width="80" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="prompt_tokens" label="输入 Token" width="100" />
          <el-table-column prop="completion_tokens" label="输出 Token" width="100" />
          <el-table-column prop="total_tokens" label="总 Token" width="100" />
          <el-table-column prop="duration_ms" label="耗时" width="90">
            <template #default="{ row }">
              {{ row.duration_ms ? `${(row.duration_ms / 1000).toFixed(1)}s` : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" min-width="160" />
        </el-table>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { adminApi } from '@/api/admin'
import { useLoading } from '@/composables/useLoading'

const route = useRoute()
const { loading, withLoading } = useLoading()
const detail = ref(null)

const statusMap = { pending: '等待中', streaming: '生成中', completed: '已完成', failed: '失败', canceled: '已取消' }
const statusTypeMap = { pending: 'info', streaming: 'warning', completed: 'success', failed: 'danger', canceled: 'info' }
const transportMap = { driving: '自驾', transit: '公共交通', walking: '步行', cycling: '骑行', mixed: '混合' }
const mapExport = computed(() => detail.value?.snapshots?.map_exports?.[0] || null)

function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function transportLabel(t) { return transportMap[t] || t }

const fetchDetail = withLoading(async () => {
  const res = await adminApi.getRecordDetail(route.params.recordId)
  detail.value = res.data
})

onMounted(() => fetchDetail())
</script>

<style lang="scss" scoped>
.back-bar { margin-bottom: 16px; }
h3 { margin-bottom: 20px; }
.detail-table { margin-bottom: 24px; max-width: 720px; }

.section-title {
  margin: 24px 0 12px;
  font-size: 15px;
  color: $text-primary;
}

.info-block {
  margin-bottom: 10px;
  font-size: 14px;
}

.route-map-preview {
  margin-top: 8px;

  img {
    max-width: 520px;
    width: 100%;
    border: 1px solid #ebeef5;
    border-radius: 6px;
  }
}

.block-label {
  font-weight: 500;
  color: $text-secondary;
}

.md-content {
  background: #f9fafb;
  padding: 16px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
  margin-top: 8px;
}
</style>
