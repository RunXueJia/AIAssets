import { createApp } from 'vue'
import { createPinia } from 'pinia'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import { setupGuards } from './router/guard'

import './styles/global.scss'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Element Plus Chinese locale
app.config.globalProperties.$ELEMENT = { locale: zhCn }

setupGuards(router)

app.mount('#app')
