import http from '@/utils/http'

export const adminApi = {
  // Users
  getUsers(params) {
    return http.get('/api/v1/admin/users', { params })
  },
  getUserDetail(userId) {
    return http.get(`/api/v1/admin/users/${userId}`)
  },
  disableUser(userId) {
    return http.post(`/api/v1/admin/users/${userId}/disable`)
  },
  enableUser(userId) {
    return http.post(`/api/v1/admin/users/${userId}/enable`)
  },

  // Generation Records
  getRecords(params) {
    return http.get('/api/v1/admin/generation_records', { params })
  },
  getRecordDetail(recordId) {
    return http.get(`/api/v1/admin/generation_records/${recordId}`)
  },
  retryRecord(recordId) {
    return http.post(`/api/v1/admin/generation_records/${recordId}/retry`)
  },
  deleteRecord(recordId) {
    return http.delete(`/api/v1/admin/generation_records/${recordId}`)
  },

  // LLM Configs
  getLlmConfigs(params) {
    return http.get('/api/v1/admin/llm_configs', { params })
  },
  getLlmConfigDetail(configId) {
    return http.get(`/api/v1/admin/llm_configs/${configId}`)
  },
  createLlmConfig(data) {
    return http.post('/api/v1/admin/llm_configs', data)
  },
  updateLlmConfig(configId, data) {
    return http.put(`/api/v1/admin/llm_configs/${configId}`, data)
  },
  testLlmConfig(configId, testPrompt) {
    return http.post(`/api/v1/admin/llm_configs/${configId}/test`, {
      test_prompt: testPrompt,
    })
  },
  testLlmConfigStream(configId, testPrompt, token, signal) {
    return fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/llm_configs/${configId}/test_stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({ test_prompt: testPrompt }),
      signal,
    })
  },
  enableLlmConfig(configId) {
    return http.post(`/api/v1/admin/llm_configs/${configId}/enable`)
  },
  disableLlmConfig(configId) {
    return http.post(`/api/v1/admin/llm_configs/${configId}/disable`)
  },

  // External helper APIs. These use the shared admin HTTP client so the
  // Authorization header is always attached by the request interceptor.
  searchAmapPlaces(params) {
    return http.get('/api/v1/amap/search_places', { params })
  },
  calculateAmapRoute(data) {
    return http.post('/api/v1/amap/calculate_route', data)
  },
  exportAmapRouteMap(data) {
    return http.post('/api/v1/amap/export_route_map', data)
  },
  queryWeather(params) {
    return http.get('/api/v1/weather/query', { params })
  },
  batchWeatherSummary(data) {
    return http.post('/api/v1/weather/batch_summary', data)
  },
  searchRealtime(params) {
    return http.get('/api/v1/realtime/search', { params })
  },
}
