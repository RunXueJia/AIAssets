const mockTopics = [
  { id: 'topic_001', task_id: 'task_001', title: '用 AI 10 分钟写完一份周报', audience: '普通职场人', angle: '把零散工作记录整理成可提交周报', column: '一分钟 AI 办公', duration_seconds: 60, keywords: ['AI 写周报', '职场效率', '办公自动化'], reason: '主题具体，适合演示。', status: 'draft', need_human_confirm: false, created_at: '2026-05-20 09:20:00' },
  { id: 'topic_002', task_id: 'task_001', title: 'AI 帮你整理会议纪要的 3 个步骤', audience: '职场新人', angle: '从录音到结构化纪要', column: '一分钟 AI 办公', duration_seconds: 60, keywords: ['AI 会议纪要', '职场效率'], reason: '实用性强。', status: 'draft', need_human_confirm: false, created_at: '2026-05-20 09:20:00' },
  { id: 'topic_003', task_id: 'task_001', title: '不会写邮件？让 AI 帮你草拟', audience: '普通职场人', angle: 'AI 写邮件模板和润色', column: '普通人 AI 工具箱', duration_seconds: 45, keywords: ['AI 写邮件', '职场沟通'], reason: '高频场景', status: 'approved', need_human_confirm: false, created_at: '2026-05-20 09:20:00' },
]

export default {
  'GET:/topic/get_topic_list': (params) => ({
    code: 0, message: 'success',
    data: { items: mockTopics, total: mockTopics.length, page: params?.page || 1, page_size: params?.page_size || 20 },
  }),

  'GET:/topic/get_topic_detail/{id}': (params, id) => {
    const topic = mockTopics.find((t) => t.id === id) || mockTopics[0]
    return {
      code: 0, message: 'success',
      data: {
        ...topic,
        source_summary_id: 'sum_001',
        source_items: [],
      },
    }
  },

  'POST:/topic/change_topic_status': (data) => ({
    code: 0, message: 'success', data: { topic_id: data.topic_id, status: data.status },
  }),

  'POST:/topic/generate_script': (data) => ({
    code: 0, message: 'success',
    data: { task_id: 'task_002', topic_id: data.topic_id, status: 'pending', stream_url: '/api/v1/generation/stream/task_002' },
  }),
}
