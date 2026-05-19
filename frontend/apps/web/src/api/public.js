import { apiClient } from '@/utils/apiClient'

const get = (url, params) => apiClient.get(url, { params })
const post = (url, data) => apiClient.post(url, data)

export const publicApi = {
  getHomeData: () => get('/public/home/get_home_data'),
  getColumns: (params) => get('/public/columns/get_column_list', params),
  getColumnDetail: (id) => get(`/public/columns/get_column_detail/${id}`),
  getArticles: (params) => get('/public/articles/get_article_list', params),
  getArticleDetail: (slug) => get(`/public/articles/get_article_detail/${slug}`),
  getVideoDetail: (id) => get(`/public/videos/get_video_detail/${id}`),
  getDownloadAssets: (params) => get('/public/download_assets/get_download_asset_list', params),
  getTools: (params) => get('/public/tools/get_tool_recommendation_list', params),
  submitLead: (data) => post('/public/leads/submit_lead', data),
  requestDownload: (data) => post('/public/downloads/request_download', data),
  trackEvent: (data) => post('/public/analytics/track_event', data)
}
