<template>
  <component :is="layout">
    <router-view />
  </component>
</template>

<script setup>
import { useIsMobile } from '@/composables/useIsMobile'
import DesktopLayout from '@/layouts/DesktopLayout.vue'
import MobileLayout from '@/layouts/MobileLayout.vue'
import { computed } from 'vue'

const { isMobile } = useIsMobile()
const layout = computed(() => isMobile.value ? MobileLayout : DesktopLayout)
</script>
