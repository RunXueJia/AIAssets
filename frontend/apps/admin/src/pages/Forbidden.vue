<template>
  <main class="forbidden surface">
    <h1>403</h1>
    <p>当前账号没有访问该页面的权限。</p>
    <el-button
      type="primary"
      @click="$router.push('/dashboard')"
    >
      返回看板
    </el-button>
  </main>
</template>

<style scoped lang="scss">
.forbidden {
  width: 420px;
  margin: 12vh auto;
  padding: 34px;
  text-align: center;

  h1 {
    margin: 0;
    color: var(--h24-danger);
    font-size: 64px;
  }

  p {
    margin: 10px 0 22px;
    color: var(--h24-muted);
  }
}
</style>
