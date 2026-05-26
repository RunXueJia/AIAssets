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

if (typeof window !== 'undefined') {
  const pressSelector = [
    'button:not(:disabled)',
    '.el-button:not(.is-disabled)',
    'a.nav-pill',
    'a.login-link',
    '.tab-item',
    '.transport-option',
    '.tag-item',
    '.people-btn',
    '.picker-trigger',
    '.record-card',
    '.recent-card',
  ].join(',')
  let pressedTarget = null

  document.addEventListener('pointerdown', (event) => {
    const target = event.target instanceof Element ? event.target.closest(pressSelector) : null
    if (!target) return
    pressedTarget?.classList.remove('neu-pressed')
    pressedTarget = target
    pressedTarget.classList.add('neu-pressed')
  }, true)

  const clearPressed = () => {
    pressedTarget?.classList.remove('neu-pressed')
    pressedTarget = null
  }

  document.addEventListener('pointerup', clearPressed, true)
  document.addEventListener('pointercancel', clearPressed, true)
  document.addEventListener('pointerleave', clearPressed, true)
  window.addEventListener('blur', clearPressed)
}
