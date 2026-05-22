<template>
  <div class="users-page">
    <div class="page-header">
      <h3>用户管理</h3>
    </div>

    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索用户名、昵称或邮箱"
        clearable
        style="width: 260px"
        @keyup.enter="search"
      />
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 120px" @change="search">
        <el-option label="正常" value="active" />
        <el-option label="已禁用" value="disabled" />
      </el-select>
      <el-select v-model="roleFilter" placeholder="角色" clearable style="width: 120px" @change="search">
        <el-option label="用户" value="user" />
        <el-option label="游客" value="guest" />
        <el-option label="管理员" value="admin" />
      </el-select>
      <el-button type="primary" @click="search">查询</el-button>
    </div>

    <el-table :data="users" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" min-width="120" />
      <el-table-column prop="nickname" label="昵称" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="160">
        <template #default="{ row }">{{ row.email || '-' }}</template>
      </el-table-column>
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">{{ roleLabel(row.role) }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
            {{ row.status === 'active' ? '正常' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_login_at" label="最后登录" min-width="160" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="$router.push(`/users/${row.id}`)">详情</el-button>
          <el-popconfirm
            v-if="row.status === 'active'"
            title="确认禁用该用户？"
            @confirm="handleDisable(row)"
          >
            <template #reference>
              <el-button text type="danger">禁用</el-button>
            </template>
          </el-popconfirm>
          <el-popconfirm
            v-else
            title="确认启用该用户？"
            @confirm="handleEnable(row)"
          >
            <template #reference>
              <el-button text type="success">启用</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :total="total"
        :page-size="pageSize"
        layout="total, prev, pager, next"
        @current-change="fetchUsers"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import { useLoading } from '@/composables/useLoading'

const { loading, withLoading } = useLoading()
const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const keyword = ref('')
const statusFilter = ref('')
const roleFilter = ref('')

function roleLabel(r) {
  const map = { admin: '管理员', user: '用户', guest: '游客' }
  return map[r] || r
}

const fetchUsers = withLoading(async () => {
  const params = { page: page.value, page_size: pageSize }
  if (keyword.value) params.keyword = keyword.value
  if (statusFilter.value) params.status = statusFilter.value
  if (roleFilter.value) params.role = roleFilter.value
  const res = await adminApi.getUsers(params)
  users.value = res.data?.items || []
  total.value = res.data?.total || 0
})

function search() {
  page.value = 1
  fetchUsers()
}

async function handleDisable(row) {
  try {
    await adminApi.disableUser(row.id)
    ElMessage.success('已禁用')
    fetchUsers()
  } catch { /* ignore */ }
}

async function handleEnable(row) {
  try {
    await adminApi.enableUser(row.id)
    ElMessage.success('已启用')
    fetchUsers()
  } catch { /* ignore */ }
}

onMounted(() => fetchUsers())
</script>

<style lang="scss" scoped>
.page-header {
  margin-bottom: 20px;
  h3 { font-size: 18px; }
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
