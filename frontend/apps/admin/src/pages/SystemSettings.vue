<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">
          系统配置
        </h1>
        <p class="page-subtitle">
          权限点、角色概览、系统配置和操作审计预留。
        </p>
      </div>
    </div>

    <div class="system-grid">
      <section class="surface panel">
        <h2>当前用户</h2>
        <el-descriptions
          :column="1"
          border
        >
          <el-descriptions-item label="账号">
            {{ auth.user?.username }}
          </el-descriptions-item>
          <el-descriptions-item label="名称">
            {{ auth.user?.display_name }}
          </el-descriptions-item>
          <el-descriptions-item label="角色">
            {{ auth.user?.roles?.join(', ') }}
          </el-descriptions-item>
        </el-descriptions>
      </section>

      <section class="surface panel">
        <h2>权限点</h2>
        <el-collapse>
          <el-collapse-item
            v-for="group in permissionGroups"
            :key="group.title"
            :title="group.title"
          >
            <div class="permission-list">
              <el-tag
                v-for="permission in group.permissions"
                :key="permission"
                effect="plain"
              >
                {{ permission }}
              </el-tag>
            </div>
          </el-collapse-item>
        </el-collapse>
      </section>
    </div>

    <section class="surface panel">
      <h2>配置项</h2>
      <el-form label-width="150px">
        <el-form-item label="对象存储">
          <el-input
            model-value="S3 / MinIO 待后端接入"
            disabled
          />
        </el-form-item>
        <el-form-item label="任务默认并发">
          <el-input-number
            :model-value="3"
            disabled
          />
        </el-form-item>
        <el-form-item label="密钥展示策略">
          <el-input
            model-value="仅返回脱敏值，例如 sk-***abcd"
            disabled
          />
        </el-form-item>
      </el-form>
    </section>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/store/auth'
import { permissionGroups } from '@/utils/permissions'

const auth = useAuthStore()
</script>

<style scoped lang="scss">
.system-grid {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  gap: 16px;
}

.panel {
  padding: 16px;

  h2 {
    margin: 0 0 14px;
    font-size: 18px;
  }
}

.permission-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
