<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面不存在</p>
    <el-button @click="$router.replace('/')">回到首页</el-button>
  </div>
</template>

<style lang="scss" scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  gap: 16px;

  h1 { font-size: 64px; color: $text-secondary; }
  p { color: $text-secondary; }
}
</style>
