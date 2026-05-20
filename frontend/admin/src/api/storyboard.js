import request from './request'

export function updateStoryboard(scriptId, items) {
  return request.post('/storyboard/update_storyboard', { script_id: scriptId, items }).then((r) => r.data)
}
