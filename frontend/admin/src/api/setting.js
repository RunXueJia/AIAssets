import request from './request'

export function getSetting() {
  return request.get('/setting/get_setting').then((r) => r.data)
}

export function updateSetting(params) {
  return request.post('/setting/update_setting', params).then((r) => r.data)
}
