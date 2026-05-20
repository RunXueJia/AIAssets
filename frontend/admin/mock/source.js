const mockSources = [
  { id: 'src_001', task_id: 'task_001', title: 'AI 写周报的 5 个技巧', site_name: '少数派', url: 'https://example.com/1', published_at: '2026-05-19 12:00:00', summary: '文章介绍了用 AI 整理工作记录并生成周报的方法。', relevance_reason: '与 AI 写周报主题高度相关', key_points: ['整理本周事项', '生成结构化周报', '人工校对事实'], status: 'usable', need_human_confirm: false },
  { id: 'src_002', task_id: 'task_001', title: '职场人必备的 AI 效率工具', site_name: '36氪', url: 'https://example.com/2', published_at: '2026-05-18 10:00:00', summary: '盘点当前流行的 AI 办公工具。', relevance_reason: '与职场效率相关', key_points: ['工具对比', '使用场景'], status: 'usable', need_human_confirm: false },
  { id: 'src_003', task_id: 'task_001', title: '为什么你的周报总写不好', site_name: '知乎', url: 'https://example.com/3', published_at: '2026-05-17 08:00:00', summary: '分析周报写作的常见问题。', relevance_reason: '提供周报写作痛点分析', key_points: ['目标不清', '缺乏结构'], status: 'usable', need_human_confirm: false },
]

export default {
  'GET:/source/get_source_list': (params) => ({
    code: 0, message: 'success',
    data: { items: mockSources, total: mockSources.length, page: params?.page || 1, page_size: params?.page_size || 20 },
  }),

  'GET:/source/get_summary_detail/{id}': (params, id) => ({
    code: 0, message: 'success',
    data: {
      id, task_id: 'task_001', title: 'AI 写周报素材汇总',
      summary: '本次素材集中在周报结构化、工作记录整理和人工校对三个方向。',
      key_points: ['AI 适合整理素材', '关键事实仍需人工确认', '输出后要补充具体数据'],
      risk_notes: ['不要夸大为完全自动完成工作汇报'],
      source_count: 20, usable_source_count: 16, need_human_confirm: true,
      created_at: '2026-05-20 09:15:00',
    },
  }),

  'POST:/source/mark_source_status': (data) => ({
    code: 0, message: 'success', data: { source_id: data.source_id, status: data.status },
  }),
}
