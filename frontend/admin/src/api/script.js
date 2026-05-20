import request from './request'

export function getScriptDetail(id) {
  return request.get(`/script/get_script_detail/${id}`).then((r) => r.data)
}

export function updateScript(params) {
  return request.post('/script/update_script', params).then((r) => r.data)
}
