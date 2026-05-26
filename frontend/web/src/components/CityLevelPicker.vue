<template>
  <div ref="rootRef" class="city-level-picker" :class="{ 'is-mobile': isMobile, 'is-disabled': disabled }">
    <el-popover
      v-if="!isMobile"
      v-model:visible="visible"
      trigger="manual"
      placement="bottom-start"
      :show-arrow="false"
      :width="popoverWidth"
      :teleported="true"
      popper-class="city-level-popper"
    >
      <template #reference>
        <div class="trigger-shell" :class="{ open: visible, filled: !!displayValue }">
          <button
            type="button"
            class="picker-trigger"
            :disabled="disabled"
            :aria-expanded="visible"
            :aria-label="label || placeholder"
            @click="openPanel"
          >
            <span class="trigger-leading">
              <el-icon class="trigger-icon"><Location /></el-icon>
            </span>
            <span class="trigger-body">
              <span v-if="label" class="trigger-label">{{ label }}</span>
              <span class="trigger-value" :class="{ placeholder: !displayValue }">
                {{ displayValue || placeholder }}
              </span>
            </span>
            <el-icon class="trigger-caret"><ArrowDown /></el-icon>
          </button>
          <button
            v-if="clearable && displayValue && !disabled"
            type="button"
            class="trigger-clear"
            aria-label="清除选择"
            @click.stop="clearSelection"
          >
            <el-icon><CircleClose /></el-icon>
          </button>
        </div>
      </template>

      <div class="picker-panel">
        <div class="panel-head">
          <div class="panel-path" :class="{ placeholder: !panelPath }">
            {{ panelPath || placeholder }}
          </div>
          <button v-if="clearable && displayValue" type="button" class="panel-clear" @click="clearSelection">
            清除
          </button>
        </div>

        <div class="panel-grid">
          <section class="panel-column">
            <div class="column-head">省份</div>
            <el-scrollbar class="column-scroll">
              <template v-if="loading">
                <div class="column-empty">加载中...</div>
              </template>
              <template v-else-if="provinces.length">
                <button
                  v-for="province in provinces"
                  :key="province.id"
                  type="button"
                  class="picker-item"
                  :class="{ active: province.province === activeProvinceName }"
                  @click="selectProvince(province)"
                >
                  <span class="item-text">{{ province.province }}</span>
                </button>
              </template>
              <div v-else class="column-empty">暂无数据</div>
            </el-scrollbar>
          </section>

          <section class="panel-column">
            <div class="column-head">城市</div>
            <el-scrollbar class="column-scroll">
              <template v-if="loading">
                <div class="column-empty">加载中...</div>
              </template>
              <template v-else-if="cityOptions.length">
                <button
                  v-for="city in cityOptions"
                  :key="city.id"
                  type="button"
                  class="picker-item"
                  :class="{ active: city.city === activeCityName }"
                  @click="selectCity(city)"
                >
                  <span class="item-text">{{ city.city }}</span>
                </button>
              </template>
              <div v-else class="column-empty">请选择省份</div>
            </el-scrollbar>
          </section>

          <section class="panel-column">
            <div class="column-head">县 / 区</div>
            <el-scrollbar class="column-scroll">
              <template v-if="loading">
                <div class="column-empty">加载中...</div>
              </template>
              <template v-else-if="countyOptions.length">
                <button
                  v-for="county in countyOptions"
                  :key="county"
                  type="button"
                  class="picker-item"
                  :class="{ active: county === activeCountyName }"
                  @click="selectCounty(county)"
                >
                  <span class="item-text">{{ county }}</span>
                </button>
              </template>
              <div v-else class="column-empty">请选择城市</div>
            </el-scrollbar>
          </section>
        </div>
      </div>
    </el-popover>

    <template v-else>
      <div class="trigger-shell mobile-shell" :class="{ open: visible, filled: !!displayValue }">
        <button
          type="button"
          class="picker-trigger"
          :disabled="disabled"
          :aria-expanded="visible"
          :aria-label="label || placeholder"
          @click="openPanel"
        >
          <span class="trigger-leading">
            <el-icon class="trigger-icon"><Location /></el-icon>
          </span>
          <span class="trigger-body">
            <span v-if="label" class="trigger-label">{{ label }}</span>
            <span class="trigger-value" :class="{ placeholder: !displayValue }">
              {{ displayValue || placeholder }}
            </span>
          </span>
          <el-icon class="trigger-caret"><ArrowDown /></el-icon>
        </button>
        <button
          v-if="clearable && displayValue && !disabled"
          type="button"
          class="trigger-clear"
          aria-label="清除选择"
          @click.stop="clearSelection"
        >
          <el-icon><CircleClose /></el-icon>
        </button>
      </div>

      <el-drawer
        v-model="visible"
        direction="btt"
        :size="drawerSize"
        :show-close="false"
        :with-header="false"
        :lock-scroll="false"
        append-to-body
        modal-class="city-level-drawer-mask"
        class="city-level-drawer"
      >
        <div class="drawer-shell">
          <div class="drawer-handle"></div>
          <div class="panel-head">
            <div class="panel-path" :class="{ placeholder: !panelPath }">
              {{ panelPath || placeholder }}
            </div>
            <button v-if="clearable && displayValue" type="button" class="panel-clear" @click="clearSelection">
              清除
            </button>
          </div>

          <div class="mobile-tabs">
            <button
              v-for="level in mobileLevels"
              :key="level.key"
              type="button"
              class="mobile-tab"
              :class="{ active: activeLevel === level.key, disabled: level.disabled }"
              :disabled="level.disabled"
              @click="activeLevel = level.key"
            >
              {{ level.label }}
            </button>
          </div>

          <div class="mobile-list-wrap">
            <el-scrollbar v-if="activeLevel === 'province'" class="mobile-scroll">
              <template v-if="loading">
                <div class="column-empty">加载中...</div>
              </template>
              <template v-else-if="provinces.length">
                <button
                  v-for="province in provinces"
                  :key="province.id"
                  type="button"
                  class="picker-item mobile-item"
                  :class="{ active: province.province === activeProvinceName }"
                  @click="selectProvince(province)"
                >
                  <span class="item-text">{{ province.province }}</span>
                </button>
              </template>
              <div v-else class="column-empty">暂无数据</div>
            </el-scrollbar>

            <el-scrollbar v-else-if="activeLevel === 'city'" class="mobile-scroll">
              <template v-if="loading">
                <div class="column-empty">加载中...</div>
              </template>
              <template v-else-if="cityOptions.length">
                <button
                  v-for="city in cityOptions"
                  :key="city.id"
                  type="button"
                  class="picker-item mobile-item"
                  :class="{ active: city.city === activeCityName }"
                  @click="selectCity(city)"
                >
                  <span class="item-text">{{ city.city }}</span>
                </button>
              </template>
              <div v-else class="column-empty">请选择省份</div>
            </el-scrollbar>

            <el-scrollbar v-else class="mobile-scroll">
              <template v-if="loading">
                <div class="column-empty">加载中...</div>
              </template>
              <template v-else-if="countyOptions.length">
                <button
                  v-for="county in countyOptions"
                  :key="county"
                  type="button"
                  class="picker-item mobile-item"
                  :class="{ active: county === activeCountyName }"
                  @click="selectCounty(county)"
                >
                  <span class="item-text">{{ county }}</span>
                </button>
              </template>
              <div v-else class="column-empty">请选择城市</div>
            </el-scrollbar>
          </div>
        </div>
      </el-drawer>
    </template>
  </div>
</template>

<script setup>
import { ArrowDown, CircleClose, Location } from '@element-plus/icons-vue'
import { computed, onMounted, ref, watch, onBeforeUnmount } from 'vue'
import { useIsMobile } from '@/composables/useIsMobile'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '请选择省 / 市 / 县',
  },
  label: {
    type: String,
    default: '',
  },
  clearable: {
    type: Boolean,
    default: true,
  },
  initialValue: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'change', 'clear'])

const { isMobile } = useIsMobile()
const rootRef = ref(null)
const visible = ref(false)
const loading = ref(true)
const provinces = ref([])
const activeProvinceName = ref('')
const activeCityName = ref('')
const activeCountyName = ref('')
const activeLevel = ref('province')
const viewportHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 800)
let resizeHandler = null

let cityTreePromise = null

const displayValue = computed(() => props.modelValue?.trim() || '')
const panelPath = computed(() => {
  const parts = [activeProvinceName.value, activeCityName.value, activeCountyName.value].filter(Boolean)
  return parts.join(' / ')
})

const activeProvinceItem = computed(() => (
  provinces.value.find(item => item.province === activeProvinceName.value) || null
))
const cityOptions = computed(() => activeProvinceItem.value?.citys || [])
const activeCityItem = computed(() => (
  cityOptions.value.find(item => item.city === activeCityName.value) || null
))
const countyOptions = computed(() => activeCityItem.value?.areas || [])
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)
const popoverWidth = computed(() => Math.min(760, Math.max(560, viewportWidth.value - 48)))
const drawerSize = computed(() => (viewportHeight.value < 700 ? '86%' : '78%'))
const mobileLevels = computed(() => ([
  { key: 'province', label: '省份', disabled: false },
  { key: 'city', label: '城市', disabled: !activeProvinceName.value },
  { key: 'county', label: '县 / 区', disabled: !activeCityName.value },
]))

function normalizeCityTree(raw) {
  if (!Array.isArray(raw)) return []
  return raw
    .map((province, provinceIndex) => {
      const citys = Array.isArray(province?.citys)
        ? province.citys.map((city, cityIndex) => {
          const seen = new Set()
          const areas = []
          for (const area of Array.isArray(city?.areas) ? city.areas : []) {
            const name = area?.area?.trim()
            if (!name || seen.has(name)) continue
            seen.add(name)
            areas.push(name)
          }
          if (!areas.length && city?.city) areas.push(city.city)
          return {
            id: `${provinceIndex}-${cityIndex}-${city?.city || 'city'}`,
            city: city?.city || '',
            areas,
          }
        }).filter(item => item.city)
        : []

      return {
        id: `${provinceIndex}-${province?.province || 'province'}`,
        province: province?.province || '',
        citys,
      }
    })
    .filter(item => item.province)
}

function parseParts(value) {
  return String(value)
    .split(/\s*(?:\/|·|—|>|-)\s*/)
    .map(part => part.trim())
    .filter(Boolean)
}

function resetDraft() {
  activeProvinceName.value = ''
  activeCityName.value = ''
  activeCountyName.value = ''
  activeLevel.value = 'province'
}

function syncFromValue(value) {
  if (!value) {
    resetDraft()
    return
  }

  const parts = parseParts(value)
  if (parts.length < 3 || !provinces.value.length) return

  const province = provinces.value.find(item => item.province === parts[0])
  if (!province) return

  const city = province.citys.find(item => item.city === parts[1])
  if (!city) return

  const county = city.areas.find(name => name === parts[2]) || city.areas[0] || ''
  activeProvinceName.value = province.province
  activeCityName.value = city.city
  activeCountyName.value = county
  activeLevel.value = 'county'
}

async function ensureCityTree() {
  loading.value = true
  try {
    if (!cityTreePromise) {
      cityTreePromise = fetch(`${import.meta.env.BASE_URL}city.json`)
        .then(async (response) => {
          if (!response.ok) {
            throw new Error(`加载城市数据失败：${response.status}`)
          }
          const data = await response.json()
          return normalizeCityTree(data)
        })
        .catch((error) => {
          cityTreePromise = null
          throw error
        })
    }

    provinces.value = await cityTreePromise
    syncFromValue(props.modelValue)
  } catch {
    provinces.value = []
    resetDraft()
  } finally {
    loading.value = false
  }
}

function openPanel() {
  if (props.disabled) return
  visible.value = true
  if (displayValue.value) {
    syncFromValue(displayValue.value)
  }
  else if (!activeProvinceName.value) {
    activeLevel.value = 'province'
  }
}

function emitSelection() {
  if (!activeProvinceName.value || !activeCityName.value || !activeCountyName.value) return
  const value = [activeProvinceName.value, activeCityName.value, activeCountyName.value].join(' / ')
  emit('update:modelValue', value)
  emit('change', {
    province: activeProvinceName.value,
    city: activeCityName.value,
    county: activeCountyName.value,
    value,
  })
}

function selectProvince(province) {
  activeProvinceName.value = province.province
  activeCityName.value = ''
  activeCountyName.value = ''
  activeLevel.value = 'city'
}

function selectCity(city) {
  activeCityName.value = city.city
  activeCountyName.value = ''
  activeLevel.value = 'county'
}

function selectCounty(county) {
  activeCountyName.value = county
  emitSelection()
  visible.value = false
}

function clearSelection() {
  emit('update:modelValue', '')
  emit('clear')
  resetDraft()
}

function handleOutsideClick(event) {
  if (isMobile.value || !visible.value) return
  const target = event.target
  if (!(target instanceof Node)) return
  if (rootRef.value?.contains(target)) return
  if (typeof target.closest === 'function' && target.closest('.city-level-popper')) return
  visible.value = false
}

watch(
  () => props.modelValue,
  (value) => {
    if (!value) {
      resetDraft()
      return
    }
    if (provinces.value.length) {
      syncFromValue(value)
    }
  },
)

watch(
  () => props.initialValue,
  (value) => {
    if (props.modelValue) return
    if (!value || !provinces.value.length) return
    const next = String(value).trim()
    if (!next) return
    syncFromValue(next)
    if (activeProvinceName.value && activeCityName.value && activeCountyName.value) {
      emit('update:modelValue', [activeProvinceName.value, activeCityName.value, activeCountyName.value].join(' / '))
    }
  },
  { immediate: true },
)

watch(visible, (nextVisible) => {
  if (isMobile.value) return
  const method = nextVisible ? 'addEventListener' : 'removeEventListener'
  document[method]('pointerdown', handleOutsideClick, true)
}, { immediate: true })

onMounted(() => {
  ensureCityTree()
  resizeHandler = () => {
    viewportHeight.value = window.innerHeight
    viewportWidth.value = window.innerWidth
  }
  window.addEventListener('resize', resizeHandler)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleOutsideClick, true)
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }
})
</script>

<style scoped lang="scss">
.city-level-picker {
  width: 100%;
  min-width: 0;
}

.city-level-picker.error .picker-trigger {
  border-color: rgba($color-danger, 0.62);
  box-shadow:
    0 0 0 2px rgba($color-danger, 0.3) inset,
    0 8px 16px rgba(176, 168, 144, 0.18) inset;
}

:global(.city-level-popper) {
  padding: 0 !important;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 10px;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 12%, rgba(255, 255, 255, 0.92), transparent 54%),
    linear-gradient(145deg, rgba(255, 255, 252, 0.96), rgba(228, 225, 214, 0.92));
  box-shadow: $shadow-lg;
}

:global(.city-level-drawer) {
  .el-drawer__body {
    padding: 0;
  }
}

.trigger-shell {
  position: relative;
  width: 100%;
}

.picker-trigger {
  width: 100%;
  min-height: 48px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 52px 10px 14px;
  border: 1px solid rgba(255, 255, 255, 0.58);
  border-radius: 8px;
  background:
    radial-gradient(circle at 18% 20%, rgba(255, 255, 255, 1), rgba(255, 255, 255, 0.62) 42%, transparent 70%),
    linear-gradient(145deg, rgba(255, 255, 252, 0.98), rgba(228, 225, 213, 0.86));
  color: #252522;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease,
    background 0.18s ease;

  &:hover:not(:disabled) {
    border-color: rgba(255, 255, 255, 0.84);
    box-shadow:
      0 1px 1px rgba(255, 255, 255, 0.92) inset,
      0 -10px 18px rgba(184, 176, 151, 0.1) inset,
      0 13px 22px rgba(89, 95, 98, 0.16);
    transform: translateY(-1px);
  }

  &:focus-visible {
    outline: none;
    border-color: rgba(255, 255, 255, 0.88);
    box-shadow:
      0 0 0 2px rgba(255, 255, 255, 0.54) inset,
      0 10px 18px rgba(89, 95, 98, 0.16);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.66;
  }
}

.trigger-shell.open .picker-trigger,
.trigger-shell.filled .picker-trigger {
  border-color: rgba(255, 255, 255, 0.7);
}

.trigger-leading {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  border-radius: 50%;
  background:
    radial-gradient(circle at 50% 28%, rgba(255, 255, 255, 1), rgba(248, 248, 241, 0.96) 52%, #d7d9d3 100%);
  color: #4d555d;
  box-shadow: 0 5px 9px rgba(63, 72, 80, 0.16) inset;
}

.trigger-icon {
  font-size: 16px;
}

.trigger-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.trigger-label {
  font-size: $font-size-xs;
  line-height: 1.2;
  color: #667078;
  font-weight: 600;
}

.trigger-value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: $font-size-sm;
  line-height: 1.35;
  font-weight: 600;

  &.placeholder {
    color: #667078;
    font-weight: 500;
  }
}

.trigger-caret {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #59636b;
  font-size: 16px;
  pointer-events: none;
}

.trigger-clear {
  position: absolute;
  right: 36px;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  color: #59636b;
  cursor: pointer;

  &:hover {
    color: #252a2e;
  }
}

.picker-panel {
  min-width: 0;
  padding: 16px;
  background: $content-bg;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 6px 12px;
}

.panel-path {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: $text-primary;
  font-size: $font-size-sm;
  font-weight: 650;
}

.panel-path.placeholder {
  color: $text-hint;
  font-weight: 500;
}

.panel-clear {
  flex: 0 0 auto;
  border: none;
  background: none;
  color: $color-link;
  font-size: $font-size-xs;
  font-weight: 600;
  cursor: pointer;
  padding: 0;

  &:hover {
    text-decoration: underline;
  }
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.panel-column {
  min-width: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background:
    linear-gradient(145deg, rgba(255, 255, 252, 0.8), rgba(229, 226, 214, 0.62));
  overflow: hidden;
}

.column-head {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: $font-size-xs;
  font-weight: 700;
  color: $text-secondary;
  background: rgba(255, 255, 255, 0.44);
}

.column-scroll {
  height: 318px;
}

.picker-item {
  width: 100%;
  min-height: 42px;
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: transparent;
  color: $text-secondary;
  cursor: pointer;
  text-align: left;
  transition: background 0.16s ease, color 0.16s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.48);
    color: $text-primary;
  }

  &.active {
    background:
      radial-gradient(circle at 50% 18%, rgba(255, 255, 255, 1), transparent 58%),
      linear-gradient(145deg, rgba(255, 255, 252, 0.98), rgba(226, 223, 211, 0.88));
    color: #252a2e;
    font-weight: 650;
    box-shadow:
      0 1px 1px rgba(255, 255, 255, 0.88) inset,
      0 7px 13px rgba(89, 95, 98, 0.14);
  }
}

.item-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.column-empty {
  min-height: 318px;
  display: grid;
  place-items: center;
  color: $text-hint;
  font-size: $font-size-sm;
}

.mobile-shell {
  margin-bottom: 0;
}

.mobile-tabs {
  display: flex;
  gap: 8px;
  padding: 0 4px 12px;
}

.mobile-tab {
  flex: 1;
  min-height: 40px;
  border: 1px solid rgba(255, 255, 255, 0.54);
  border-radius: 8px;
  background:
    radial-gradient(circle at 50% 18%, rgba(255, 255, 255, 0.96), transparent 58%),
    linear-gradient(145deg, rgba(255, 255, 252, 0.96), rgba(226, 223, 211, 0.86));
  color: #4c555d;
  font-size: $font-size-sm;
  font-weight: 650;
  cursor: pointer;

  &.active {
    border-color: rgba(255, 255, 255, 0.7);
    background:
      radial-gradient(circle at 50% 70%, #d9d9d1, #f6f5eb 58%, #ffffff 100%);
    color: #22272b;
    box-shadow:
      0 7px 14px rgba(74, 83, 90, 0.22) inset,
      0 -1px 0 rgba(255, 255, 255, 0.72) inset;
  }

  &.disabled {
    opacity: 0.54;
    cursor: not-allowed;
  }
}

.mobile-list-wrap {
  min-height: 0;
  height: calc(100% - 104px);
}

.mobile-scroll {
  height: 100%;
}

.mobile-item {
  min-height: 46px;
  border-bottom: 1px solid rgba($border-card, 0.58);
}

.drawer-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 14px 16px calc(16px + env(safe-area-inset-bottom, 0));
  background: $content-bg;
  border-radius: 28px 28px 0 0;
}

.drawer-handle {
  width: 42px;
  height: 4px;
  align-self: center;
  margin-bottom: 10px;
  border-radius: 999px;
  background: rgba($text-hint, 0.28);
}

.is-disabled {
  pointer-events: none;
}

@media (max-width: 767px) {
  .picker-trigger {
    min-height: 50px;
    padding-right: 50px;
  }

  .trigger-clear {
    right: 34px;
  }

  .mobile-list-wrap {
    height: calc(100% - 100px);
  }
}

// Neumorphic soft UI override
:global(.city-level-popper) {
  border: 0;
  background: $content-bg !important;
  border-radius: 24px;
  box-shadow: $shadow-lg;
}

:global(.city-level-drawer-mask.el-overlay) {
  background-color: rgba(47, 55, 66, 0.28) !important;
  overflow: hidden !important;
}

:global(.city-level-drawer-mask.el-overlay .el-drawer),
:global(.city-level-drawer.el-drawer) {
  display: flex !important;
  flex-direction: column;
  position: absolute !important;
  right: 0 !important;
  bottom: 0 !important;
  left: 0 !important;
  width: 100% !important;
  min-height: 320px;
  background: $content-bg !important;
  border-radius: 28px 28px 0 0 !important;
  overflow: hidden !important;
  box-shadow:
    -10px -10px 20px rgba(255, 255, 255, 0.7),
    10px 10px 24px rgba(163, 177, 198, 0.42) !important;
}

:global(.city-level-drawer-mask.el-overlay .el-drawer__body),
:global(.city-level-drawer.el-drawer .el-drawer__body) {
  flex: 1;
  min-height: 0;
  padding: 0 !important;
  background: $content-bg !important;
  border-radius: 28px 28px 0 0;
  overflow: hidden;
}

.picker-trigger,
.mobile-tab {
  border: 0;
  background: $content-bg;
  color: $text-primary;
  box-shadow: $shadow-sm;
}

.picker-trigger:hover:not(:disabled),
.mobile-tab:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: $shadow-md;
}

.trigger-shell.open .picker-trigger,
.trigger-shell.filled .picker-trigger,
.picker-trigger:active,
.mobile-tab.active {
  background: $content-bg;
  box-shadow:
    inset -5px -5px 10px rgba(255, 255, 255, 0.68),
    inset 5px 5px 10px rgba(163, 177, 198, 0.42);
}

.trigger-leading {
  background: $content-bg;
  color: $color-primary-dark;
  box-shadow:
    inset -3px -3px 6px rgba(255, 255, 255, 0.7),
    inset 3px 3px 6px rgba(163, 177, 198, 0.36);
}

.panel-column,
.drawer-shell {
  border: 0;
  background: $content-bg;
  box-shadow:
    inset -6px -6px 12px rgba(255, 255, 255, 0.54),
    inset 6px 6px 12px rgba(163, 177, 198, 0.22);
}

.panel-grid,
.mobile-list-wrap {
  padding: 8px;
  border-radius: 22px;
  background: $content-bg;
  box-shadow:
    inset -7px -7px 14px rgba(255, 255, 255, 0.58),
    inset 7px 7px 14px rgba(163, 177, 198, 0.22);
}

.panel-grid {
  gap: 12px;
}

.mobile-tabs {
  padding: 2px 4px 14px;
}

.column-head {
  background: transparent;
  border-bottom-color: rgba(163, 177, 198, 0.18);
}

.picker-item:hover,
.picker-item.active {
  background: $content-bg;
  color: $text-primary;
  box-shadow:
    inset -4px -4px 8px rgba(255, 255, 255, 0.58),
    inset 4px 4px 8px rgba(163, 177, 198, 0.28);
}
</style>
