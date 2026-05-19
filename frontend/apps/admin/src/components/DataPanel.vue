<template>
  <section class="surface">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="keyword"
          clearable
          placeholder="搜索关键词"
          style="width: 240px"
          @keyup.enter="emitSearch"
          @clear="emitSearch"
        />
        <slot name="filters" />
        <el-button
          :icon="Search"
          @click="emitSearch"
        >
          查询
        </el-button>
      </div>
      <div class="toolbar-right">
        <slot name="actions" />
      </div>
    </div>
    <el-table
      v-loading="loading"
      :data="items"
      border
      stripe
      height="420"
      empty-text="暂无数据"
      class="data-table"
    >
      <slot />
    </el-table>
    <div class="pagination">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next"
        :total="total"
        :current-page="page"
        :page-size="pageSize"
        @current-change="$emit('update:page', $event)"
        @size-change="$emit('update:pageSize', $event)"
      />
    </div>
  </section>
</template>

<script setup>
import { Search } from '@element-plus/icons-vue'
import { ref, watch } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  total: {
    type: Number,
    default: 0
  },
  loading: {
    type: Boolean,
    default: false
  },
  page: {
    type: Number,
    default: 1
  },
  pageSize: {
    type: Number,
    default: 20
  },
  search: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['search', 'update:page', 'update:pageSize'])
const keyword = ref(props.search)

watch(
  () => props.search,
  (value) => {
    keyword.value = value
  }
)

function emitSearch() {
  emit('search', keyword.value)
}
</script>

<style scoped lang="scss">
.data-table {
  border-right: 0;
  border-left: 0;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  padding: 14px;
}
</style>
