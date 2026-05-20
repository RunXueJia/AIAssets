import request from './request'

export function updateSubtitle(scriptId, items) {
  return request.post('/subtitle/update_subtitle', { script_id: scriptId, items }).then((r) => r.data)
}
