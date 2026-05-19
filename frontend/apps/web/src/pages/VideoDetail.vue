<template>
  <main class="page-wrap video-page">
    <section class="video-box">
      <div class="video-placeholder">
        视频播放器预留
      </div>
    </section>
    <section>
      <h1>{{ video.title }}</h1>
      <p>分辨率 {{ video.resolution }} · 时长 {{ video.duration_seconds }} 秒</p>
      <router-link
        class="button"
        to="/downloads"
      >
        下载配套资料
      </router-link>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { publicApi } from '@/api/public'

const route = useRoute()
const video = ref({})

onMounted(async () => {
  video.value = await publicApi.getVideoDetail(route.params.id)
})
</script>

<style scoped lang="scss">
.video-page {
  display: grid;
  grid-template-columns: 0.85fr 1fr;
  gap: 28px;
  align-items: center;
}

.video-box {
  aspect-ratio: 9 / 16;
  max-height: 620px;
  border-radius: 8px;
  background: #102326;
}

.video-placeholder {
  display: grid;
  place-items: center;
  height: 100%;
  color: #d9eeee;
}

h1 {
  margin: 0;
  font-size: 46px;
  line-height: 1.12;
}

p {
  color: var(--web-muted);
  font-size: 18px;
}

@media (width <= 840px) {
  .video-page {
    grid-template-columns: 1fr;
  }
}
</style>
