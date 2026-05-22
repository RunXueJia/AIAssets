import { ref } from 'vue'

export function useLoading(initialState = false) {
  const loading = ref(initialState)

  function withLoading(fn) {
    return async (...args) => {
      loading.value = true
      try {
        return await fn(...args)
      } finally {
        loading.value = false
      }
    }
  }

  return { loading, withLoading }
}
