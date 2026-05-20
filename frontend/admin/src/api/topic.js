import request from './request'

export function getTopicList(params) {
  return request.get('/topic/get_topic_list', params).then((r) => r.data)
}

export function getTopicDetail(id) {
  return request.get(`/topic/get_topic_detail/${id}`).then((r) => r.data)
}

export function changeTopicStatus(topicId, status, reason) {
  return request.post('/topic/change_topic_status', { topic_id: topicId, status, reason }).then((r) => r.data)
}

export function generateScript(topicId, startMode) {
  return request.post('/topic/generate_script', { topic_id: topicId, start_mode: startMode || 'now' }).then((r) => r.data)
}
