<template>
  <main class="page-wrap">
    <h1>内容栏目</h1>
    <p class="lead">
      按栏目浏览 AI 办公、自动化和增长内容。
    </p>
    <div class="card-grid">
      <article
        v-for="column in columns"
        :key="column.id"
        class="content-card"
      >
        <h3>{{ column.name }}</h3>
        <p>{{ column.description }}</p>
        <small>{{ column.default_duration }}</small>
      </article>
    </div>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { publicApi } from '@/api/public'

const columns = ref([])

onMounted(async () => {
  const data = await publicApi.getColumns()
  columns.value = data.items
})
</script>

<style scoped lang="scss">
h1 {
  margin: 0;
  font-size: 42px;
}

.lead {
  color: var(--web-muted);
  font-size: 18px;
}

small {
  display: inline-block;
  margin-top: 14px;
  color: var(--web-primary);
  font-weight: 700;
}
</style>
