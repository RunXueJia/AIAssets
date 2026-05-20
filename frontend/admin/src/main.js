import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import request from './api/request'
import './styles/global.scss'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

async function bootstrap() {
  if (USE_MOCK) {
    const mockModules = import.meta.glob('/mock/*.js', { eager: true })
    const allHandlers = {}
    for (const [path, mod] of Object.entries(mockModules)) {
      if (path.includes('index.js')) continue
      if (mod.default && typeof mod.default === 'object') {
        Object.assign(allHandlers, mod.default)
      }
    }
    request.registerMock(allHandlers)
    console.log(`[Mock] Registered ${Object.keys(allHandlers).length} mock handlers`)
  }

  const app = createApp(App)

  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  app.use(createPinia())
  app.use(router)
  app.use(ElementPlus, { locale: zhCn })
  app.mount('#app')
}

bootstrap()
