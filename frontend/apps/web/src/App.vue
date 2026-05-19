<template>
  <div>
    <header class="site-header">
      <router-link
        to="/"
        class="brand"
      >
        <span>24</span>
        <strong>Hours24</strong>
      </router-link>
      <nav>
        <router-link to="/columns">
          栏目
        </router-link>
        <router-link to="/downloads">
          资料包
        </router-link>
        <router-link to="/tools">
          工具推荐
        </router-link>
        <a href="/login">后台入口</a>
      </nav>
    </header>
    <router-view />
    <footer class="site-footer">
      <strong>Hours24</strong>
      <span>AI 内容资产生产系统公开站 MVP</span>
    </footer>
  </div>
</template>
