<template>
  <div class="script-detail">
    <page-header title="脚本与分镜">
      <template #actions>
        <el-button @click="$router.back()">返回</el-button>
        <el-button type="primary" @click="saveAll">保存所有修改</el-button>
      </template>
    </page-header>

    <el-tabs v-model="activeTab" type="card">
      <el-tab-pane label="脚本内容" name="script">
        <script-form v-if="detail.script" :script="detail.script" :readonly="false" @update="onScriptUpdate" />
      </el-tab-pane>
      <el-tab-pane label="分镜表" name="storyboard">
        <storyboard-table :items="detail.storyboards || []" :readonly="false" @update="onStoryboardUpdate" />
      </el-tab-pane>
      <el-tab-pane label="字幕" name="subtitle">
        <subtitle-list :items="detail.subtitles || []" :readonly="false" @update="onSubtitleUpdate" />
      </el-tab-pane>
      <el-tab-pane label="版本记录" name="versions">
        <el-table :data="detail.versions || []" size="small">
          <el-table-column prop="version" label="版本号" width="80" />
          <el-table-column prop="operator_name" label="操作人" width="120" />
          <el-table-column prop="created_at" label="创建时间" width="170" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getScriptDetail, updateScript } from '@/api/script'
import { updateStoryboard } from '@/api/storyboard'
import { updateSubtitle } from '@/api/subtitle'
import PageHeader from '@/components/common/PageHeader.vue'
import ScriptForm from '@/components/script/ScriptForm.vue'
import StoryboardTable from '@/components/script/StoryboardTable.vue'
import SubtitleList from '@/components/script/SubtitleList.vue'

const route = useRoute()
const activeTab = ref('script')
const detail = reactive({ script: null, storyboards: [], subtitles: [], versions: [] })

let pendingScript = null
let pendingStoryboard = null
let pendingSubtitle = null

function onScriptUpdate(data) { pendingScript = data }
function onStoryboardUpdate(data) { pendingStoryboard = data }
function onSubtitleUpdate(data) { pendingSubtitle = data }

async function fetchDetail() {
  try {
    const data = await getScriptDetail(route.params.id)
    detail.script = data.script
    detail.storyboards = data.storyboards || []
    detail.subtitles = data.subtitles || []
    detail.versions = data.versions || []
  } catch {}
}

async function saveAll() {
  const scriptId = detail.script?.id
  if (!scriptId) return

  try {
    if (pendingScript) await updateScript({ script_id: scriptId, ...pendingScript })
    if (pendingStoryboard) await updateStoryboard(scriptId, pendingStoryboard)
    if (pendingSubtitle) await updateSubtitle(scriptId, pendingSubtitle)
    ElMessage.success('保存成功')
    await fetchDetail()
  } catch {}
}

onMounted(() => fetchDetail())
</script>
