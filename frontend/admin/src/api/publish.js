import request from './request'

export function createRecord(params) {
  return request.post('/publish/create_record', params).then((r) => r.data)
}

export function updateRecord(params) {
  return request.post('/publish/update_record', params).then((r) => r.data)
}

export function getRecordList(params) {
  return request.get('/publish/get_record_list', params).then((r) => r.data)
}
