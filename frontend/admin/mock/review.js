const reviewItems = [
  { content_id: 'script_001', content_type: 'script', title: '用 AI 10 分钟写完一份周报', status: 'pending_review', need_human_confirm: true, risk_notes: ['涉及效率提升，需避免夸张承诺'], created_by_name: '系统生成', created_at: '2026-05-20 09:30:00' },
  { content_id: 'script_002', content_type: 'script', title: 'AI 会议纪要整理技巧', status: 'pending_review', need_human_confirm: false, risk_notes: [], created_by_name: '系统生成', created_at: '2026-05-20 09:45:00' },
]

export default {
  'GET:/review/get_review_list': (params) => ({
    code: 0, message: 'success',
    data: { items: reviewItems, total: reviewItems.length, page: params?.page || 1, page_size: params?.page_size || 20 },
  }),

  'POST:/review/approve': (data) => ({
    code: 0, message: 'success',
    data: { content_id: data.content_id, status: 'approved', next_status: 'pending_render' },
  }),

  'POST:/review/approve_with_edit': (data) => ({
    code: 0, message: 'success',
    data: { content_id: data.content_id, status: 'approved_with_edit', version: 2, next_status: 'pending_render' },
  }),

  'POST:/review/reject': (data) => ({
    code: 0, message: 'success', data: { content_id: data.content_id, status: 'rejected' },
  }),

  'POST:/review/regenerate': (data) => ({
    code: 0, message: 'success',
    data: { task_id: 'task_003', status: 'pending', stream_url: '/api/v1/generation/stream/task_003' },
  }),
}
