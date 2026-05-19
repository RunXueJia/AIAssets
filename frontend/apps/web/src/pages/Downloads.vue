<template>
  <main class="page-wrap download-page">
    <section>
      <h1>资料包下载</h1>
      <p class="lead">
        选择资料包并提交授权信息，获取下载入口。
      </p>
      <div class="card-grid">
        <button
          v-for="asset in assets"
          :key="asset.id"
          class="content-card asset-button"
          :class="{ active: selected?.id === asset.id }"
          @click="selected = asset"
        >
          <h3>{{ asset.title }}</h3>
          <p>{{ asset.summary }}</p>
        </button>
      </div>
    </section>
    <form
      class="lead-form content-card"
      @submit.prevent="submit"
    >
      <h3>申请下载</h3>
      <label>姓名<input
        v-model="form.name"
        required
      ></label>
      <label>联系方式<input
        v-model="form.contact"
        required
      ></label>
      <label>公司<input v-model="form.company"></label>
      <label>角色<input v-model="form.role"></label>
      <label class="consent"><input
        v-model="form.consent"
        type="checkbox"
        required
      > 我同意提交信息用于资料发送</label>
      <button
        class="button"
        type="submit"
      >
        提交并获取
      </button>
      <p
        v-if="result"
        class="result"
      >
        {{ result }}
      </p>
    </form>
  </main>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { publicApi } from '@/api/public'

const assets = ref([])
const selected = ref(null)
const result = ref('')
const form = reactive({ name: '', contact: '', company: '', role: '', consent: false })

onMounted(async () => {
  const data = await publicApi.getDownloadAssets()
  assets.value = data.items
  selected.value = data.items[0]
})

async function submit() {
  const lead = {
    ...form,
    need_type: 'download_asset',
    source_page: '/downloads',
    source_asset_id: selected.value?.id
  }
  await publicApi.submitLead(lead)
  await publicApi.requestDownload(lead)
  result.value = '提交成功，后端接入后这里会返回真实下载地址。'
}
</script>

<style scoped lang="scss">
.download-page {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 24px;
}

h1 {
  margin: 0;
  font-size: 42px;
}

.lead {
  color: var(--web-muted);
  font-size: 18px;
}

.asset-button {
  cursor: pointer;
  text-align: left;
}

.asset-button.active {
  border-color: var(--web-primary);
  background: var(--web-soft);
}

.lead-form {
  display: grid;
  align-self: start;
  gap: 14px;
}

.consent {
  grid-template-columns: 18px 1fr;
  align-items: center;
}

.result {
  margin: 0;
  color: var(--web-primary);
}

@media (width <= 860px) {
  .download-page {
    grid-template-columns: 1fr;
  }
}
</style>
