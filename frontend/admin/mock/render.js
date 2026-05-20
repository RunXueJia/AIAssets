const renderItems = [
  { id: 'render_001', script_id: 'script_001', title: '用 AI 10 分钟写完一份周报', status: 'success', progress: 100, video_id: 'video_001', duration_seconds: 60, error_message: '', created_at: '2026-05-20 10:30:00', updated_at: '2026-05-20 10:40:00' },
  { id: 'render_002', script_id: 'script_002', title: 'AI 会议纪要整理技巧', status: 'rendering', progress: 65, video_id: '', duration_seconds: 0, error_message: '', created_at: '2026-05-20 10:35:00', updated_at: '2026-05-20 10:38:00' },
]

export default {
  'POST:/render/create_render_task': (data) => ({
    code: 0, message: 'success', data: { render_task_id: 'render_003', status: 'pending' },
  }),

  'GET:/render/get_render_list': (params) => ({
    code: 0, message: 'success',
    data: { items: renderItems, total: renderItems.length, page: params?.page || 1, page_size: params?.page_size || 20 },
  }),

  'POST:/render/retry_render': (data) => ({
    code: 0, message: 'success', data: { render_task_id: data.render_task_id, status: 'pending' },
  }),

  'GET:/render/get_video_detail/{id}': (params, id) => ({
    code: 0, message: 'success',
    data: {
      id, script_id: 'script_001', title: '用 AI 10 分钟写完一份周报',
      duration_seconds: 60, width: 1080, height: 1920, format: 'mp4',
      preview_url: `/api/v1/file/preview_video/${id}`,
      download_url: `/api/v1/file/download_video/${id}`,
      cover_url: '/api/v1/file/preview_cover/cover_001',
      created_at: '2026-05-20 10:40:00',
    },
  }),
}
