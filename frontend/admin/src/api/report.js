import request from './request'

export function getDailyReportList(params) {
  return request.get('/report/get_daily_report_list', params).then((r) => r.data)
}

export function getDailyReportDetail(id) {
  return request.get(`/report/get_daily_report_detail/${id}`).then((r) => r.data)
}

export function getReportExportUrl(id, format) {
  const base = import.meta.env.VITE_API_BASE || '/api/v1'
  return `${base}/report/export_daily_report/${id}?format=${format || 'markdown'}`
}
