<template>
  <main class="page-wrap">
    <h1>工具推荐</h1>
    <p class="lead">
      围绕办公自动化场景整理工具清单。
    </p>
    <div class="card-grid">
      <article
        v-for="tool in tools"
        :key="tool.id"
        class="content-card"
      >
        <h3>{{ tool.name }}</h3>
        <p>{{ tool.scenario }}</p>
        <p>{{ tool.reason }}</p>
      </article>
    </div>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { publicApi } from '@/api/public'

const tools = ref([])

onMounted(async () => {
  const data = await publicApi.getTools()
  tools.value = data.items
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
</style>
