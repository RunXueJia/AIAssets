import request from './request'

export function getOverview(date) {
  return request.get('/dashboard/get_overview', { params: date ? { date } : {} }).then((r) => r.data)
}

export function getTrend(range) {
  return request.get('/dashboard/get_trend', { params: range ? { range } : {} }).then((r) => r.data)
}
