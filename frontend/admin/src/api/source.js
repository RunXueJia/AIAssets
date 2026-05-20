import request from './request'

export function getSourceList(params) {
  return request.get('/source/get_source_list', params).then((r) => r.data)
}

export function getSummaryDetail(id) {
  return request.get(`/source/get_summary_detail/${id}`).then((r) => r.data)
}

export function markSourceStatus(sourceId, status, reason) {
  return request.post('/source/mark_source_status', { source_id: sourceId, status, reason }).then((r) => r.data)
}
