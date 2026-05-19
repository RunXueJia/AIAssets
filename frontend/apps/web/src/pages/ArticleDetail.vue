<template>
  <main class="page-wrap article">
    <article>
      <p class="eyebrow">
        图文指南
      </p>
      <h1>{{ article.title }}</h1>
      <p class="summary">
        {{ article.summary }}
      </p>
      <div class="body">
        {{ article.body }}
      </div>
    </article>
    <aside class="content-card">
      <h3>需要配套资料？</h3>
      <p>提交联系方式后获取资料下载入口。</p>
      <router-link
        class="button"
        to="/downloads"
      >
        申请资料
      </router-link>
    </aside>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { publicApi } from '@/api/public'

const route = useRoute()
const article = ref({})

onMounted(async () => {
  article.value = await publicApi.getArticleDetail(route.params.slug)
  publicApi.trackEvent({
    event_type: 'article_view',
    source_page: route.fullPath,
    target_id: article.value.id
  })
})
</script>

<style scoped lang="scss">
.article {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 28px;
}

.eyebrow {
  color: var(--web-primary);
  font-weight: 700;
}

h1 {
  margin: 0;
  font-size: clamp(34px, 5vw, 58px);
  line-height: 1.08;
}

.summary {
  color: var(--web-muted);
  font-size: 19px;
  line-height: 1.8;
}

.body {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--web-line);
  font-size: 18px;
  line-height: 2;
}

@media (width <= 840px) {
  .article {
    grid-template-columns: 1fr;
  }
}
</style>
