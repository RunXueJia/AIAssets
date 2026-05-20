import request from './request'

export function createTask(params) {
  return request.post('/generation/create_task', params).then((r) => r.data)
}

export function getTaskList(params) {
  return request.get('/generation/get_task_list', params).then((r) => r.data)
}

export function getTaskDetail(id) {
  return request.get(`/generation/get_task_detail/${id}`).then((r) => r.data)
}

export function cancelTask(taskId) {
  return request.post('/generation/cancel_task', { task_id: taskId }).then((r) => r.data)
}

export function retryTask(taskId, retryFromStage) {
  return request.post('/generation/retry_task', { task_id: taskId, retry_from_stage: retryFromStage }).then((r) => r.data)
}
