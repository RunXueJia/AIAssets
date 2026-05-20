const monitors = [
  { id: 'mon_001', topic: 'AI 办公工具更新', audience: '普通职场人', schedule_time: '09:00', fetch_limit: 20, auto_generate_topics: true, status: 'enabled', last_run_at: '2026-05-20 09:00:00', last_summary_id: 'sum_002', created_at: '2026-05-19 18:00:00' },
  { id: 'mon_002', topic: 'AI 绘画工具动态', audience: '设计师', schedule_time: '10:00', fetch_limit: 15, auto_generate_topics: false, status: 'paused', last_run_at: '2026-05-19 10:00:00', last_summary_id: '', created_at: '2026-05-18 14:00:00' },
]

export default {
  'POST:/monitor/create_monitor': (data) => ({
    code: 0, message: 'success',
    data: { monitor_id: 'mon_003', status: 'enabled' },
  }),

  'GET:/monitor/get_monitor_list': (params) => ({
    code: 0, message: 'success',
    data: { items: monitors, total: monitors.length, page: params?.page || 1, page_size: params?.page_size || 20 },
  }),

  'GET:/monitor/get_monitor_detail/{id}': (params, id) => {
    const m = monitors.find((x) => x.id === id) || monitors[0]
    return { code: 0, message: 'success', data: { ...m, updated_at: '2026-05-20 09:00:00' } }
  },

  'POST:/monitor/update_monitor': (data) => ({
    code: 0, message: 'success', data: { monitor_id: data.monitor_id, status: 'enabled' },
  }),

  'POST:/monitor/change_monitor_status': (data) => ({
    code: 0, message: 'success', data: { monitor_id: data.monitor_id, status: data.status },
  }),

  'GET:/monitor/get_daily_summary_list': (params) => ({
    code: 0, message: 'success',
    data: {
      items: [
        { summary_id: 'sum_002', monitor_id: 'mon_001', topic: 'AI 办公工具更新', date: '2026-05-20', source_count: 20, topic_count: 10, status: 'success', created_at: '2026-05-20 09:10:00' },
      ],
      total: 1, page: params?.page || 1, page_size: params?.page_size || 20,
    },
  }),
}
