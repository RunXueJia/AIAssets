import http from '@/utils/http'

export const planningApi = {
  generateStream(data) {
    // Returns fetch response for SSE parsing
    const auth = JSON.parse(localStorage.getItem('access_token') || '""')
    return fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/planning/generate_stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: auth ? `Bearer ${auth}` : '',
      },
      body: JSON.stringify(data),
    })
  },

  cancel(recordId) {
    return http.post(`/api/v1/planning/cancel/${recordId}`)
  },

  getRecords(params) {
    return http.get('/api/v1/planning/records', { params })
  },

  getRecordDetail(recordId) {
    return http.get(`/api/v1/planning/records/${recordId}`)
  },

  regenerate(recordId, overrideInput) {
    return http.post(`/api/v1/planning/records/${recordId}/regenerate`, {
      override_input: overrideInput,
    })
  },

  getRouteMap(recordId) {
    return http.get(`/api/v1/planning/records/${recordId}/route_map`)
  },
}
