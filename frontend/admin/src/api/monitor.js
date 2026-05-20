import request from './request'

export function createMonitor(params) {
  return request.post('/monitor/create_monitor', params).then((r) => r.data)
}

export function getMonitorList(params) {
  return request.get('/monitor/get_monitor_list', params).then((r) => r.data)
}

export function getMonitorDetail(id) {
  return request.get(`/monitor/get_monitor_detail/${id}`).then((r) => r.data)
}

export function updateMonitor(params) {
  return request.post('/monitor/update_monitor', params).then((r) => r.data)
}

export function changeMonitorStatus(monitorId, status) {
  return request.post('/monitor/change_monitor_status', { monitor_id: monitorId, status }).then((r) => r.data)
}

export function getDailySummaryList(params) {
  return request.get('/monitor/get_daily_summary_list', params).then((r) => r.data)
}
