<template>
  <main class="page-wrap">
    <section class="hero">
      <div>
        <h1>Hours24 AI 办公效率内容库</h1>
        <p>浏览短视频教程、图文指南、资料包和工具清单，把高频办公场景拆成可执行步骤。</p>
        <router-link
          class="button"
          to="/downloads"
        >
          查看资料包
        </router-link>
      </div>
      <div class="visual-board">
        <div class="board-row strong">
          最新内容生产闭环
        </div>
        <div class="board-row">
          选题生成 -> 脚本审核 -> 分镜合成 -> 发布包
        </div>
        <div class="board-metrics">
          <span>视频 10</span>
          <span>图文 10</span>
          <span>资料 5</span>
        </div>
      </div>
    </section>

    <h2 class="section-title">
      最新图文
    </h2>
    <div class="card-grid">
      <router-link
        v-for="article in home.latest_articles"
        :key="article.id"
        class="content-card"
        :to="`/articles/${article.slug}`"
      >
        <h3>{{ article.title }}</h3>
        <p>{{ article.summary }}</p>
      </router-link>
    </div>

    <h2 class="section-title">
      热门栏目
    </h2>
    <div class="card-grid">
      <article
        v-for="column in home.hot_columns"
        :key="column.id"
        class="content-card"
      >
        <h3>{{ column.name }}</h3>
        <p>{{ column.description }}</p>
      </article>
    </div>
  </main>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { publicApi } from '@/api/public'

const home = reactive({ latest_articles: [], hot_columns: [], download_assets: [], tools: [] })

onMounted(async () => {
  Object.assign(home, await publicApi.getHomeData())
})
</script>

<style scoped lang="scss">
.board-row {
  padding: 14px;
  border: 1px solid var(--web-line);
  border-radius: 8px;
  background: #fff;
  color: var(--web-muted);

  & + & {
    margin-top: 12px;
  }
}

.strong {
  color: var(--web-text);
  font-size: 22px;
  font-weight: 700;
}

.board-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 18px;

  span {
    padding: 18px 10px;
    border-radius: 8px;
    background: var(--web-soft);
    text-align: center;
    font-weight: 700;
  }
}
</style>
