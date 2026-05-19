<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">
          审核工作台
        </h1>
        <p class="page-subtitle">
          集中处理脚本、分镜、视频和图文页的通过、驳回与修改后通过。
        </p>
      </div>
    </div>

    <DataPanel
      :items="queue.items"
      :total="queue.total"
      :loading="loading"
      @search="handleSearch"
    >
      <el-table-column
        prop="platform_title"
        label="内容标题"
        min-width="220"
      />
      <el-table-column
        prop="hook"
        label="开头"
        min-width="180"
      />
      <el-table-column
        label="风险提示"
        min-width="220"
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
      <el-table-column
        label="操作"
        width="240"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            text
            type="success"
            @click="approve(row)"
          >
            通过
          </el-button>
          <el-button
            text
            type="primary"
            @click="openChange(row)"
          >
            修改后通过
          </el-button>
          <el-button
            text
            type="danger"
            @click="openReject(row)"
          >
            驳回
          </el-button>
        </template>
      </el-table-column>
    </DataPanel>

    <el-dialog
      v-model="rejectVisible"
      title="驳回原因"
      width="520px"
    >
      <el-input
        v-model="rejectReason"
        type="textarea"
        :rows="5"
        placeholder="请输入驳回原因"
      />
      <template #footer>
        <el-button @click="rejectVisible = false">
          取消
        </el-button>
        <el-button
          type="danger"
          @click="submitReject"
        >
          确认驳回
        </el-button>
      </template>
    </el-dialog>

    <el-drawer
      v-model="changeVisible"
      title="修改后通过"
      size="640"
    >
      <el-form label-position="top">
        <el-form-item label="平台标题">
          <el-input v-model="editing.platform_title" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input
            v-model="editing.platform_description"
            type="textarea"
            :rows="4"
          />
        </el-form-item>
        <el-form-item label="结尾">
          <el-input
            v-model="editing.ending"
            type="textarea"
            :rows="4"
          />
        </el-form-item>
        <el-button
          type="primary"
          @click="submitChange"
        >
          保存并通过
        </el-button>
      </el-form>
    </el-drawer>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import DataPanel from '@/components/DataPanel.vue'
import StatusTag from '@/components/StatusTag.vue'
import { reviewApi } from '@/api'

const loading = ref(false)
const queue = reactive({ items: [], total: 0 })
const rejectVisible = ref(false)
const changeVisible = ref(false)
const rejectReason = ref('')
const currentRow = ref(null)
const editing = reactive({})

async function load(keyword = '') {
  loading.value = true
  try {
    const data = await reviewApi.getQueue({ keyword })
    queue.items = data.items
    queue.total = data.total
  } finally {
    loading.value = false
  }
}

function handleSearch(keyword) {
  load(keyword)
}

async function approve(row) {
  await reviewApi.approve({ target_type: 'script', target_id: row.id, comment: '内容可发布' })
  ElMessage.success('已审核通过')
  load()
}

function openReject(row) {
  currentRow.value = row
  rejectReason.value = ''
  rejectVisible.value = true
}

async function submitReject() {
  await reviewApi.reject({ target_type: 'script', target_id: currentRow.value.id, reason: rejectReason.value })
  ElMessage.success('已驳回')
  rejectVisible.value = false
  load()
}

function openChange(row) {
  currentRow.value = row
  Object.assign(editing, row)
  changeVisible.value = true
}

async function submitChange() {
  await reviewApi.approveWithChanges({ target_type: 'script', target_id: currentRow.value.id, changes: editing })
  ElMessage.success('修改版本已通过')
  changeVisible.value = false
  load()
}

onMounted(load)
</script>
