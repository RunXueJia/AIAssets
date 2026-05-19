<template>
  <slot v-if="auth.can(permission)" />
</template>

<script setup>
import { useAuthStore } from '@/store/auth'

defineProps({
  permission: {
    type: [String, Array],
    default: ''
  }
})

const auth = useAuthStore()
</script>
