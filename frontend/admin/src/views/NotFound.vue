<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面不存在</p>
    <el-button @click="$router.replace('/dashboard')">回到首页</el-button>
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
  padding: 32px;
  text-align: center;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  box-shadow: $shadow-card;

  h1 { font-size: 64px; color: $text-primary; }
  p { color: $text-secondary; }
}
</style>
