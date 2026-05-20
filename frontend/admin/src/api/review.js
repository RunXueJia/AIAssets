import request from './request'

export function getReviewList(params) {
  return request.get('/review/get_review_list', params).then((r) => r.data)
}

export function approve(contentId, contentType, comment) {
  return request.post('/review/approve', { content_id: contentId, content_type: contentType, comment }).then((r) => r.data)
}

export function approveWithEdit(contentId, contentType, editedPayload, comment) {
  return request.post('/review/approve_with_edit', {
    content_id: contentId, content_type: contentType, edited_payload: editedPayload, comment,
  }).then((r) => r.data)
}

export function reject(contentId, contentType, reason) {
  return request.post('/review/reject', { content_id: contentId, content_type: contentType, reason }).then((r) => r.data)
}

export function regenerate(contentId, contentType, reason) {
  return request.post('/review/regenerate', { content_id: contentId, content_type: contentType, reason }).then((r) => r.data)
}
