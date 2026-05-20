import request from './request'

export function createRenderTask(scriptId, templateId, startMode) {
  return request.post('/render/create_render_task', { script_id: scriptId, template_id: templateId || 'default_vertical', start_mode: startMode || 'now' }).then((r) => r.data)
}

export function getRenderList(params) {
  return request.get('/render/get_render_list', params).then((r) => r.data)
}

export function retryRender(renderTaskId) {
  return request.post('/render/retry_render', { render_task_id: renderTaskId }).then((r) => r.data)
}

export function getVideoDetail(id) {
  return request.get(`/render/get_video_detail/${id}`).then((r) => r.data)
}
