import { apiClient } from '@/utils/apiClient'

const get = (url, params) => apiClient.get(url, { params })
const post = (url, data) => apiClient.post(url, data)

export const authApi = {
  login: (data) => post('/auth/login', data),
  logout: () => post('/auth/logout'),
  getCurrentUser: () => get('/auth/get_current_user')
}

export const dashboardApi = {
  getTodayOverview: () => get('/dashboard/get_today_overview'),
  getChannelPerformance: (params) => get('/dashboard/get_channel_performance', params),
  getTaskMetrics: (params) => get('/dashboard/get_task_metrics', params)
}

export const contentApi = {
  getChannels: (params) => get('/content_channels/get_content_channel_list', params),
  saveChannel: (data) =>
    post(data.id ? '/content_channels/update_content_channel' : '/content_channels/create_content_channel', data),
  changeChannelStatus: (data) => post('/content_channels/change_content_channel_status', data),
  getColumns: (params) => get('/columns/get_column_list', params),
  saveColumn: (data) => post(data.id ? '/columns/update_column' : '/columns/create_column', data),
  getTopics: (params) => get('/topics/get_topic_list', params),
  getTopicDetail: (id) => get(`/topics/get_topic_detail/${id}`),
  updateTopic: (data) => post('/topics/update_topic', data),
  lockTopic: (data) => post('/topics/lock_topic', data),
  rejectTopic: (data) => post('/topics/reject_topic', data),
  getScripts: (params) => get('/scripts/get_script_list', params),
  getScriptDetail: (id) => get(`/scripts/get_script_detail/${id}`),
  updateScript: (data) => post('/scripts/update_script', data),
  getStoryboards: (params) => get('/storyboards/get_storyboard_list', params),
  updateStoryboard: (data) => post('/storyboards/update_storyboard', data)
}

export const llmApi = {
  getProviders: (params) => get('/llm_providers/get_llm_provider_list', params),
  saveProvider: (data) =>
    post(data.id ? '/llm_providers/update_llm_provider' : '/llm_providers/create_llm_provider', data),
  getModels: (params) => get('/llm_models/get_llm_model_list', params),
  saveModel: (data) => post(data.id ? '/llm_models/update_llm_model' : '/llm_models/create_llm_model', data),
  getPrompts: (params) => get('/prompt_templates/get_prompt_template_list', params),
  getPromptDetail: (id) => get(`/prompt_templates/get_prompt_template_detail/${id}`),
  savePrompt: (data) =>
    post(data.id ? '/prompt_templates/update_prompt_template' : '/prompt_templates/create_prompt_template', data),
  publishPrompt: (data) => post('/prompt_templates/publish_prompt_template', data),
  getLogs: (params) => get('/llm_call_logs/get_llm_call_log_list', params),
  getCostSummary: (params) => get('/llm_call_logs/get_llm_cost_summary', params),
  getStreamChunks: (id) => get(`/llm_call_logs/get_llm_stream_chunks/${id}`)
}

export const reviewApi = {
  getQueue: (params) => get('/reviews/get_review_queue', params),
  getRecords: (params) => get('/reviews/get_review_records', params),
  approve: (data) => post('/reviews/approve_content', data),
  reject: (data) => post('/reviews/reject_content', data),
  approveWithChanges: (data) => post('/reviews/approve_content_with_changes', data)
}

export const assetApi = {
  getVideos: (params) => get('/videos/get_video_list', params),
  getVideoDetail: (id) => get(`/videos/get_video_detail/${id}`),
  createRenderTask: (data) => post('/videos/create_render_task', data),
  retryRenderTask: (data) => post('/videos/retry_render_task', data),
  getKnowledgeCards: (params) => get('/knowledge_cards/get_knowledge_card_list', params),
  getDownloadAssets: (params) => get('/download_assets/get_download_asset_list', params)
}

export const publishApi = {
  getQueue: (params) => get('/publish_queue/get_publish_queue_list', params),
  getPackageDetail: (id) => get(`/publish_queue/get_publish_package_detail/${id}`),
  markPublished: (data) => post('/publish_queue/mark_as_published', data),
  markOffline: (data) => post('/publish_queue/mark_as_offline', data)
}

export const reportApi = {
  getReports: (params) => get('/reports/get_daily_report_list', params),
  getReportDetail: (id) => get(`/reports/get_daily_report_detail/${id}`),
  getTasks: (params) => get('/tasks/get_task_log_list', params)
}
