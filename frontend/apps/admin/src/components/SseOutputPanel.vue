<template>
  <section class="surface sse-panel">
    <div class="sse-head">
      <div>
        <h3>{{ title }}</h3>
        <p>Chunk {{ stats.chunkCount }} · 首 token {{ stats.firstTokenMs || '-' }}ms · {{ stateText }}</p>
      </div>
      <div class="actions">
        <el-button
          :disabled="streaming"
          type="primary"
          @click="$emit('start')"
        >
          开始生成
        </el-button>
        <el-button
          :disabled="!streaming"
          @click="$emit('stop')"
        >
          中断
        </el-button>
      </div>
    </div>
    <el-tabs model-value="text">
      <el-tab-pane
        label="增量输出"
        name="text"
      >
        <pre class="stream-text">{{ text || '等待流式输出...' }}</pre>
      </el-tab-pane>
      <el-tab-pane
        label="原始 Chunk"
        name="raw"
      >
        <pre class="stream-text">{{ raw || '暂无原始分片' }}</pre>
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '流式生成'
  },
  text: {
    type: String,
    default: ''
  },
  raw: {
    type: String,
    default: ''
  },
  streaming: {
    type: Boolean,
    default: false
  },
  interrupted: {
    type: Boolean,
    default: false
  },
  stats: {
    type: Object,
    default: () => ({ chunkCount: 0, firstTokenMs: 0 })
  }
})

defineEmits(['start', 'stop'])

const stateText = computed(() => {
  if (props.streaming) {
    return '生成中'
  }
  if (props.interrupted) {
    return '已中断'
  }
  return props.text ? '已完成' : '未开始'
})
</script>

<style scoped lang="scss">
.sse-panel {
  padding: 16px;
}

.sse-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;

  h3 {
    margin: 0;
    font-size: 18px;
  }

  p {
    margin: 6px 0 0;
    color: var(--h24-muted);
    font-size: 13px;
  }
}

.actions {
  display: flex;
  gap: 8px;
}

.stream-text {
  min-height: 220px;
  max-height: 360px;
  overflow: auto;
  margin: 0;
  padding: 14px;
  border: 1px solid var(--h24-line);
  border-radius: 8px;
  background: #0d1b1e;
  color: #d7f4e8;
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
