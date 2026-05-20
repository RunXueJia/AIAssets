export default {
  'GET:/report/get_daily_report_list': (params) => ({
    code: 0, message: 'success',
    data: {
      items: [
        { id: 'report_001', date: '2026-05-20', title: '2026-05-20 每日产出报告', generation_task_count: 12, script_count: 8, video_count: 3, package_count: 2, failed_task_count: 1, created_at: '2026-05-20 23:00:00' },
        { id: 'report_002', date: '2026-05-19', title: '2026-05-19 每日产出报告', generation_task_count: 10, script_count: 6, video_count: 2, package_count: 2, failed_task_count: 0, created_at: '2026-05-19 23:00:00' },
      ],
      total: 2, page: params?.page || 1, page_size: params?.page_size || 20,
    },
  }),

  'GET:/report/get_daily_report_detail/{id}': (params, id) => ({
    code: 0, message: 'success',
    data: {
      id, date: '2026-05-20', title: '2026-05-20 每日产出报告',
      overview: { generation_task_count: 12, source_item_count: 86, topic_count: 30, script_count: 8, video_count: 3, package_count: 2, failed_task_count: 1 },
      source_summaries: [],
      generated_contents: [],
      pending_reviews: [],
      render_success_items: [],
      failed_tasks: [],
      exported_packages: [],
      tomorrow_suggestions: ['优先审核待处理脚本', '复盘合成失败原因'],
      markdown: '# 2026-05-20 每日产出报告\n\n...',
    },
  }),
}
